package com.falconiq.crawler.enrichment;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Parses rendered G2 product page HTML to extract real review data.
 *
 * <p>G2 review pages contain:
 * <ul>
 *   <li>JSON-LD with aggregateRating (rating + reviewCount)</li>
 *   <li>Review cards with "What do you like best?" / "What do you dislike?" sections</li>
 *   <li>Reviewer job titles and company info</li>
 * </ul>
 */
public class G2PageParser {

    private static final Logger logger = Logger.getLogger(G2PageParser.class.getName());
    private static final ObjectMapper mapper = new ObjectMapper();

    public G2Data parse(String html, String g2Url) {
        G2Data data = new G2Data();
        data.setG2Url(g2Url);

        try {
            Document doc = Jsoup.parse(html);

            parseJsonLd(doc, data);
            parseMetaTags(doc, data);
            parseReviewCards(doc, data);
            parseReviewerInfo(doc, data);

            logger.info("G2 page parsed: rating=" + data.getRating()
                    + " reviews=" + data.getReviewCount()
                    + " pros=" + data.getProsThemes().size()
                    + " cons=" + data.getConsThemes().size()
                    + " reviewers=" + data.getReviewerTitles().size());
        } catch (Exception e) {
            logger.log(Level.WARNING, "Failed to parse G2 page: " + g2Url, e);
        }

        return data;
    }

    private void parseJsonLd(Document doc, G2Data data) {
        for (Element script : doc.select("script[type=application/ld+json]")) {
            try {
                JsonNode json = mapper.readTree(script.data());
                extractAggregateRating(json, data);
                // Check @graph array
                if (json.has("@graph")) {
                    for (JsonNode node : json.get("@graph")) {
                        extractAggregateRating(node, data);
                    }
                }
            } catch (Exception ignored) {}
        }
    }

    private void extractAggregateRating(JsonNode json, G2Data data) {
        JsonNode ar = json.path("aggregateRating");
        if (ar.isMissingNode()) return;
        if (data.getRating() == null && ar.has("ratingValue")) {
            data.setRating(ar.get("ratingValue").asDouble());
        }
        if (data.getReviewCount() == 0) {
            if (ar.has("reviewCount")) {
                data.setReviewCount(ar.get("reviewCount").asInt());
            } else if (ar.has("ratingCount")) {
                data.setReviewCount(ar.get("ratingCount").asInt());
            }
        }
        // Description from JSON-LD
        if (data.getDescription().isEmpty() && json.has("description")) {
            data.setDescription(json.get("description").asText());
        }
    }

    private void parseMetaTags(Document doc, G2Data data) {
        // Fallback: meta tags
        if (data.getRating() == null) {
            Element rating = doc.selectFirst("meta[itemprop=ratingValue], meta[property=og:rating]");
            if (rating != null) {
                try { data.setRating(Double.parseDouble(rating.attr("content"))); }
                catch (NumberFormatException ignored) {}
            }
        }
        if (data.getReviewCount() == 0) {
            Element count = doc.selectFirst("meta[itemprop=reviewCount], meta[itemprop=ratingCount]");
            if (count != null) {
                try { data.setReviewCount(Integer.parseInt(count.attr("content").replace(",", ""))); }
                catch (NumberFormatException ignored) {}
            }
        }
        if (data.getDescription().isEmpty()) {
            Element desc = doc.selectFirst("meta[name=description]");
            if (desc != null) data.setDescription(desc.attr("content"));
        }
    }

    private void parseReviewCards(Document doc, G2Data data) {
        List<G2Data.ReviewTheme> pros = new ArrayList<>();
        List<G2Data.ReviewTheme> cons = new ArrayList<>();
        Set<String> seenPros = new LinkedHashSet<>();
        Set<String> seenCons = new LinkedHashSet<>();

        // G2 review structure: each review has pairs of question/answer divs
        // Look for text nodes containing the G2 review prompts
        Elements allElements = doc.getAllElements();

        Element currentQuestion = null;

        for (Element el : allElements) {
            String ownText = el.ownText().trim();
            if (ownText.isEmpty()) continue;

            String lower = ownText.toLowerCase();

            // Detect G2's review questions
            if (lower.contains("what do you like best") || lower.contains("what g2 reviewers liked")) {
                currentQuestion = el;
                continue;
            }
            if (lower.contains("what do you dislike") || lower.contains("what g2 reviewers disliked")) {
                currentQuestion = el;
                continue;
            }

            // If we're right after a question element, the next sibling text blocks are answers
            if (currentQuestion != null) {
                // Check if this element is a sibling or child of the question's parent
                if (isNearby(currentQuestion, el) && isReviewText(ownText)) {
                    String questionText = currentQuestion.ownText().toLowerCase();
                    if (questionText.contains("like best") || questionText.contains("liked")) {
                        if (seenPros.add(ownText)) {
                            pros.add(new G2Data.ReviewTheme(ownText, "positive"));
                        }
                    } else if (questionText.contains("dislike")) {
                        if (seenCons.add(ownText)) {
                            cons.add(new G2Data.ReviewTheme(ownText, "negative"));
                        }
                    }
                    currentQuestion = null; // consumed the answer
                }
            }
        }

        // Fallback: look for elements with data attributes or specific class patterns
        if (pros.isEmpty() && cons.isEmpty()) {
            parseReviewsBySelector(doc, pros, cons, seenPros, seenCons);
        }

        data.setProsThemes(pros.stream().limit(10).toList());
        data.setConsThemes(cons.stream().limit(10).toList());
    }

    private void parseReviewsBySelector(Document doc, List<G2Data.ReviewTheme> pros,
                                         List<G2Data.ReviewTheme> cons,
                                         Set<String> seenPros, Set<String> seenCons) {
        // Try common G2 CSS patterns for review content
        String[] prosSelectors = {
                "[data-testid*=like] p", "[class*=like-best] p",
                "[class*=pros] p", "div[id*=like] p"
        };
        String[] consSelectors = {
                "[data-testid*=dislike] p", "[class*=dislike] p",
                "[class*=cons] p", "div[id*=dislike] p"
        };

        for (String sel : prosSelectors) {
            for (Element el : doc.select(sel)) {
                String text = el.text().trim();
                if (isReviewText(text) && seenPros.add(text)) {
                    pros.add(new G2Data.ReviewTheme(text, "positive"));
                }
            }
        }
        for (String sel : consSelectors) {
            for (Element el : doc.select(sel)) {
                String text = el.text().trim();
                if (isReviewText(text) && seenCons.add(text)) {
                    cons.add(new G2Data.ReviewTheme(text, "negative"));
                }
            }
        }
    }

    private void parseReviewerInfo(Document doc, G2Data data) {
        Set<String> titles = new LinkedHashSet<>();
        Set<String> sizes = new LinkedHashSet<>();

        // Reviewer job titles
        Elements titleEls = doc.select(
                "[itemprop=jobTitle], [class*=job-title], [class*=reviewer-title],"
                + " span[class*=title]:not(h1):not(h2):not(title)");
        for (Element el : titleEls) {
            String title = el.text().trim();
            if (!title.isEmpty() && title.length() < 100 && !title.contains("<")) {
                titles.add(title);
            }
            if (titles.size() >= 15) break;
        }

        // Company sizes
        Elements sizeEls = doc.select("[class*=company-size], [class*=org-size], [class*=business-size]");
        for (Element el : sizeEls) {
            String size = el.text().trim();
            if (!size.isEmpty() && size.length() < 50) sizes.add(size);
            if (sizes.size() >= 5) break;
        }

        data.setReviewerTitles(new ArrayList<>(titles));
        data.setCompanySizes(new ArrayList<>(sizes));
    }

    private boolean isNearby(Element question, Element candidate) {
        // Check if candidate is a sibling, next element, or shares the same parent
        Element qParent = question.parent();
        Element cParent = candidate.parent();
        if (qParent == null || cParent == null) return false;
        return qParent.equals(cParent)
                || qParent.equals(cParent.parent())
                || cParent.equals(qParent.parent());
    }

    private boolean isReviewText(String text) {
        return text.length() >= 20 && text.length() <= 1000
                && !text.toLowerCase().startsWith("what do you")
                && !text.toLowerCase().startsWith("what g2");
    }
}

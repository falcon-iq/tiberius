package com.falconiq.crawler.core;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

/**
 * Heuristic detector for JS-rendered pages.
 * If extracted text is very short AND the HTML is dominated by script tags,
 * the page likely needs headless rendering to get real content.
 */
public class JsDetector {

    private static final int MIN_TEXT_LENGTH = 400;
    private static final double SCRIPT_RATIO_THRESHOLD = 0.4;

    /**
     * Returns true if the HTML likely needs JS rendering to produce meaningful content.
     */
    public static boolean needsJsRendering(String html) {
        if (html == null || html.isBlank()) {
            return false;
        }

        Document doc = Jsoup.parse(html);

        // Check 1: Is the visible text content very short?
        String bodyText = doc.body() != null ? doc.body().text() : "";
        if (bodyText.length() >= MIN_TEXT_LENGTH) {
            return false; // Enough text content — JSoup fetch is fine
        }

        // Check 2: Is the HTML dominated by script tags?
        Elements scripts = doc.select("script");
        long scriptContentLength = 0;
        for (Element script : scripts) {
            scriptContentLength += script.data().length();
            // Count inline src references as a weight too
            if (script.hasAttr("src")) {
                scriptContentLength += 200; // approximate weight for external scripts
            }
        }

        long totalHtmlLength = html.length();
        if (totalHtmlLength == 0) {
            return false;
        }

        double scriptRatio = (double) scriptContentLength / totalHtmlLength;

        // Check 3: Common SPA framework markers
        boolean hasSpaMarker = false;
        Element body = doc.body();
        if (body != null) {
            // React: <div id="root"></div> or <div id="app"></div> with no children
            Element root = doc.getElementById("root");
            Element appEl = doc.getElementById("app");
            Element nextEl = doc.getElementById("__next");
            if ((root != null && root.children().isEmpty())
                    || (appEl != null && appEl.children().isEmpty())
                    || nextEl != null) {
                hasSpaMarker = true;
            }
        }

        return scriptRatio > SCRIPT_RATIO_THRESHOLD || hasSpaMarker;
    }
}

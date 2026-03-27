package com.falconiq.crawler.enrichment;

import java.util.List;

public class G2Data {

    private Double rating;
    private int reviewCount;
    private String description;
    private String g2Url;
    private List<ReviewTheme> prosThemes;
    private List<ReviewTheme> consThemes;
    private List<String> reviewerTitles;
    private List<String> companySizes;

    public G2Data() {
        this.description = "";
        this.g2Url = "";
        this.prosThemes = List.of();
        this.consThemes = List.of();
        this.reviewerTitles = List.of();
        this.companySizes = List.of();
    }

    public Double getRating() { return rating; }
    public void setRating(Double rating) { this.rating = rating; }

    public int getReviewCount() { return reviewCount; }
    public void setReviewCount(int reviewCount) { this.reviewCount = reviewCount; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public String getG2Url() { return g2Url; }
    public void setG2Url(String g2Url) { this.g2Url = g2Url; }

    public List<ReviewTheme> getProsThemes() { return prosThemes; }
    public void setProsThemes(List<ReviewTheme> prosThemes) { this.prosThemes = prosThemes; }

    public List<ReviewTheme> getConsThemes() { return consThemes; }
    public void setConsThemes(List<ReviewTheme> consThemes) { this.consThemes = consThemes; }

    public List<String> getReviewerTitles() { return reviewerTitles; }
    public void setReviewerTitles(List<String> reviewerTitles) { this.reviewerTitles = reviewerTitles; }

    public List<String> getCompanySizes() { return companySizes; }
    public void setCompanySizes(List<String> companySizes) { this.companySizes = companySizes; }

    public static class ReviewTheme {
        private String theme;
        private String sentiment; // "positive" or "negative"
        private List<String> sampleQuotes;

        public ReviewTheme() {
            this.sampleQuotes = List.of();
        }

        public ReviewTheme(String theme, String sentiment) {
            this.theme = theme;
            this.sentiment = sentiment;
            this.sampleQuotes = List.of();
        }

        public String getTheme() { return theme; }
        public void setTheme(String theme) { this.theme = theme; }

        public String getSentiment() { return sentiment; }
        public void setSentiment(String sentiment) { this.sentiment = sentiment; }

        public List<String> getSampleQuotes() { return sampleQuotes; }
        public void setSampleQuotes(List<String> sampleQuotes) { this.sampleQuotes = sampleQuotes; }
    }
}

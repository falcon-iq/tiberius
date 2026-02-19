package com.falconiq.crawler;

import org.glassfish.jersey.jackson.JacksonFeature;
import org.glassfish.jersey.server.ResourceConfig;

public class AppConfig extends ResourceConfig {

    public AppConfig() {
        packages("com.falconiq.crawler.api");
        register(JacksonFeature.class);
    }
}

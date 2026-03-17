package com.example.api;

import com.example.domain.objects.IndustryBenchmark;
import com.example.fiq.generic.GenericBeanDescriptorFactory;
import com.example.fiq.generic.GenericBeanType;
import com.example.fiq.generic.GenericMongoCRUDService;
import com.example.fiq.generic.Filter;
import com.example.fiq.generic.FilterOperator;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.logging.Logger;

@Path("/industry-benchmarks")
public class IndustryBenchmarkResource {

    private static final Logger logger = Logger.getLogger(IndustryBenchmarkResource.class.getName());

    private final GenericMongoCRUDService<IndustryBenchmark> benchmarkService;

    public IndustryBenchmarkResource() {
        this.benchmarkService = GenericBeanDescriptorFactory.getInstance()
                .getCRUDService(GenericBeanType.INDUSTRY_BENCHMARK);
    }

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response listBenchmarks() {
        List<Filter> filters = List.of(
                new Filter("status", FilterOperator.EQUALS, List.of("COMPLETED"))
        );
        List<IndustryBenchmark> benchmarks = benchmarkService.list(filters, null, null, null);

        List<Map<String, Object>> summaries = new ArrayList<>();
        for (IndustryBenchmark b : benchmarks) {
            Map<String, Object> summary = new LinkedHashMap<>();
            summary.put("id", b.getId());
            summary.put("industryName", b.getIndustryName());
            summary.put("country", b.getCountry());
            summary.put("slug", b.getSlug());
            summary.put("generatedAt", b.getGeneratedAt());
            summary.put("companyCount", b.getCompanies() != null ? b.getCompanies().size() : 0);
            summaries.add(summary);
        }

        return Response.ok(summaries).build();
    }

    @GET
    @Path("/{slug}")
    @Produces(MediaType.APPLICATION_JSON)
    public Response getBenchmark(@PathParam("slug") String slug) {
        List<Filter> filters = List.of(
                new Filter("slug", FilterOperator.EQUALS, List.of(slug))
        );
        List<IndustryBenchmark> benchmarks = benchmarkService.list(filters, null, null, null);

        if (benchmarks.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND)
                    .entity(Map.of("error", "Benchmark not found")).build();
        }

        IndustryBenchmark benchmark = benchmarks.get(0);
        if (benchmark.getStatus() != IndustryBenchmark.Status.COMPLETED) {
            return Response.status(Response.Status.NOT_FOUND)
                    .entity(Map.of("error", "Benchmark not yet available")).build();
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("id", benchmark.getId());
        result.put("industryName", benchmark.getIndustryName());
        result.put("country", benchmark.getCountry());
        result.put("slug", benchmark.getSlug());
        result.put("generatedAt", benchmark.getGeneratedAt());
        result.put("companyCount", benchmark.getCompanies() != null ? benchmark.getCompanies().size() : 0);
        result.put("companies", benchmark.getCompanies());

        return Response.ok(result).build();
    }
}

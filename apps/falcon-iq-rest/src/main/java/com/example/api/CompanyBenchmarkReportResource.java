package com.example.api;

import com.example.domain.objects.CompanyBenchmarkReport;
import com.example.domain.objects.WebsiteCrawlDetail;
import com.example.fiq.generic.GenericBeanType;
import com.example.fiq.generic.GenericBeanDescriptorFactory;
import com.example.fiq.generic.GenericMongoCRUDService;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.logging.Logger;

@Path("/company-benchmark-report")
public class CompanyBenchmarkReportResource {

    private static final Logger logger = Logger.getLogger(CompanyBenchmarkReportResource.class.getName());

    private final GenericMongoCRUDService<WebsiteCrawlDetail> crawlDetailService;
    private final GenericMongoCRUDService<CompanyBenchmarkReport> benchmarkReportService;

    public CompanyBenchmarkReportResource() {
        this.crawlDetailService = GenericBeanDescriptorFactory.getInstance()
                .getCRUDService(GenericBeanType.WEBSITE_CRAWL_DETAIL);
        this.benchmarkReportService = GenericBeanDescriptorFactory.getInstance()
                .getCRUDService(GenericBeanType.COMPANY_BENCHMARK_REPORT);
    }

    @POST
    @Path("/start")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    @SuppressWarnings("unchecked")
    public Response start(Map<String, Object> request) {
        String userId = (String) request.get("userId");
        String companyLink = (String) request.get("companyLink");
        List<String> otherCompanyLinks = (List<String>) request.get("otherCompanyLinks");

        if (userId == null || userId.isBlank()) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(Map.of("error", "userId is required"))
                    .build();
        }
        if (companyLink == null || companyLink.isBlank()) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(Map.of("error", "companyLink is required"))
                    .build();
        }

        // Create WebsiteCrawlDetail for the main company
        WebsiteCrawlDetail companyDetail = new WebsiteCrawlDetail();
        companyDetail.setWebsiteLink(companyLink);
        companyDetail.setUserId(userId);
        companyDetail.setIsCompetitor(false);
        companyDetail.setStatus(WebsiteCrawlDetail.Status.NOT_STARTED);
        companyDetail.setNumberOfPagesCrawled(0L);
        companyDetail.setNumberOfPagesAnalyzed(0L);

        WebsiteCrawlDetail savedCompany = crawlDetailService.create(companyDetail);

        // Create WebsiteCrawlDetail for each competitor
        List<String> competitorIds = new ArrayList<>();
        if (otherCompanyLinks != null) {
            for (String link : otherCompanyLinks) {
                if (link != null && !link.isBlank()) {
                    WebsiteCrawlDetail competitorDetail = new WebsiteCrawlDetail();
                    competitorDetail.setWebsiteLink(link);
                    competitorDetail.setUserId(userId);
                    competitorDetail.setIsCompetitor(true);
                    competitorDetail.setStatus(WebsiteCrawlDetail.Status.NOT_STARTED);
                    competitorDetail.setNumberOfPagesCrawled(0L);
                    competitorDetail.setNumberOfPagesAnalyzed(0L);

                    WebsiteCrawlDetail savedCompetitor = crawlDetailService.create(competitorDetail);
                    competitorIds.add(savedCompetitor.getId());
                }
            }
        }

        // Create CompanyBenchmarkReport
        CompanyBenchmarkReport report = new CompanyBenchmarkReport();
        report.setUserId(userId);
        report.setCompanyCrawlDetailId(savedCompany.getId());
        report.setCompetitionCrawlDetailIds(competitorIds);
        report.setStatus(CompanyBenchmarkReport.Status.NOT_STARTED);

        CompanyBenchmarkReport savedReport = benchmarkReportService.create(report);

        return Response.status(Response.Status.CREATED).entity(savedReport).build();
    }
}

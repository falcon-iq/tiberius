package com.example.api;

import com.example.fiq.generic.GenericBeanMetadata;
import com.example.fiq.generic.GenericBeanType;
import com.example.fiq.generic.GenericMongoCRUDService;

import java.util.List;
import java.util.Map;

import com.example.fiq.generic.Filter;
import com.example.fiq.generic.GenericBeanDescriptorFactory;
import com.example.fiq.generic.GenericBeanFieldChangeItem;
import com.example.fiq.generic.Page;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.PUT;
import jakarta.ws.rs.DELETE;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

@Path("/generic-bean-api")
public class GenericBeanMetadataResource {

    private final GenericBeanDescriptorFactory registry = GenericBeanDescriptorFactory.getInstance();
    private final ObjectMapper mapper = new ObjectMapper();


    @GET
    @Path("/metadata/{type}")
    @Produces(MediaType.APPLICATION_JSON)
    public Response getMetadata(@PathParam("type") String typeStr) {
        GenericBeanType type;
        try {
            type = GenericBeanType.valueOf(typeStr.toUpperCase());
        } catch (IllegalArgumentException e) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity("Unknown type: " + typeStr)
                    .build();
        }

        GenericBeanMetadata meta = registry.getDescriptor(type).getGenericBeanMetadata();
        if (meta == null) {
            return Response.status(Response.Status.NOT_FOUND).entity("No metadata for type: " + type).build();
        }

        return Response.ok(meta).build();
    }

    @POST
    @Path("/read/{type}")
    @Produces(MediaType.APPLICATION_JSON)
    @Consumes(MediaType.APPLICATION_JSON)
    public Response read(@PathParam("type") String typeStr, GenericReadRequest request) {
        GenericBeanType type;
        try {
            type = GenericBeanType.valueOf(typeStr.toUpperCase());
        } catch (IllegalArgumentException e) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity("Unknown type: " + typeStr)
                    .build();
        }

        GenericBeanMetadata meta = registry.getDescriptor(type).getGenericBeanMetadata();
        if (meta == null) {
            return Response.status(Response.Status.NOT_FOUND).entity("No metadata for type: " + type).build();
        }

        // obtain service from registry and call list
        GenericMongoCRUDService<?> service = registry.getCRUDService(type);
        if (service == null) {
            return Response.status(Response.Status.NOT_IMPLEMENTED).entity("No CRUD service for type: " + type).build();
        }

        // use request's filters, page and searchString
        List<Filter> filters = null;
        Page page = null;
        String searchString = null;
        if (request != null) {
            filters = request.getFilters();
            page = request.getPage();
            searchString = request.getSearchString();
        }

        List<?> results = service.list(filters, null, page, searchString);
        return Response.ok(results).build();
    }

    @SuppressWarnings("unchecked")
    @PUT
    @Path("/update/{type}/{id}")
    @Produces(MediaType.APPLICATION_JSON)
    @Consumes(MediaType.APPLICATION_JSON)
    public Response update(@PathParam("type") String typeStr, @PathParam("id") String id,
            List<GenericBeanFieldChangeItem<?>> changeItems) {
        GenericBeanType type;
        try {
            type = GenericBeanType.valueOf(typeStr.toUpperCase());
        } catch (IllegalArgumentException e) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity("Unknown type: " + typeStr)
                    .build();
        }

        GenericBeanMetadata meta = registry.getDescriptor(type).getGenericBeanMetadata();
        if (meta == null) {
            return Response.status(Response.Status.NOT_FOUND).entity("No metadata for type: " + type).build();
        }

        GenericMongoCRUDService<?> service = registry.getCRUDService(type);
        if (service == null) {
            return Response.status(Response.Status.NOT_IMPLEMENTED).entity("No CRUD service for type: " + type).build();
        }

        // service is untyped here; perform an unchecked cast to satisfy the
        // GenericMongoCRUDService<T>.update signature. This is safe because the
        // registry controls service creation for each type.
        @SuppressWarnings("rawtypes")
        Boolean ok = ((GenericMongoCRUDService) service).update(id, (List) changeItems);
        return Response.ok(Map.of("updated", ok)).build();
    }

    @POST
    @Path("/create/{type}")
    @Produces(MediaType.APPLICATION_JSON)
    @Consumes(MediaType.APPLICATION_JSON)
    public Response createByType(@PathParam("type") String typeStr, JsonNode body) {
        GenericBeanType type;
        try {
            type = GenericBeanType.valueOf(typeStr.toUpperCase());
        } catch (IllegalArgumentException e) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity("Unknown type: " + typeStr)
                    .build();
        }

        GenericBeanMetadata meta = registry.getDescriptor(type).getGenericBeanMetadata();
        if (meta == null) {
            return Response.status(Response.Status.NOT_FOUND).entity("No metadata for type: " + type).build();
        }

        GenericMongoCRUDService<?> service = registry.getCRUDService(type);
        if (service == null) {
            return Response.status(Response.Status.NOT_IMPLEMENTED).entity("No CRUD service for type: " + type).build();
        }

        Object responseObject = service.createFromJson(body, mapper);
        return Response.status(Response.Status.CREATED).entity(responseObject).build();
    }

    @DELETE
    @Path("/delete/{type}/{id}")
    @Produces(MediaType.APPLICATION_JSON)
    public Response delete(@PathParam("type") String typeStr, @PathParam("id") String id) {
        GenericBeanType type;
        try {
            type = GenericBeanType.valueOf(typeStr.toUpperCase());
        } catch (IllegalArgumentException e) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity("Unknown type: " + typeStr)
                    .build();
        }

        GenericBeanMetadata meta = registry.getDescriptor(type).getGenericBeanMetadata();
        if (meta == null) {
            return Response.status(Response.Status.NOT_FOUND).entity("No metadata for type: " + type).build();
        }

        GenericMongoCRUDService<?> service = registry.getCRUDService(type);
        if (service == null) {
            return Response.status(Response.Status.NOT_IMPLEMENTED).entity("No CRUD service for type: " + type).build();
        }

        Boolean deleted = service.delete(id);
        return Response.ok(Map.of("deleted", deleted)).build();
    }
}

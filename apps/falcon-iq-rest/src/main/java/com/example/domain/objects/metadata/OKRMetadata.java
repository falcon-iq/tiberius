package com.example.domain.objects.metadata;

import java.util.List;

import com.example.fiq.generic.FieldType;
import com.example.fiq.generic.GenericBeanFieldMetadata;
import com.example.fiq.generic.GenericBeanFieldMetadataBuilder;
import com.example.fiq.generic.GenericBeanMetadata;
import com.example.fiq.generic.GenericBeanType;

public class OKRMetadata implements GenericBeanMetadata {

	private static final GenericBeanFieldMetadata<String> ID =
		GenericBeanFieldMetadataBuilder.<String>builder()
			.name("_id")
			.label("Id")
			.type(FieldType.STRING)
			.required(false)
            .updateAllowed(false)
			.hidden(true)
			.sortSupported(true)
			.filterSupported(true)
			.build();
    
	public static final GenericBeanFieldMetadata<String> OBJECTIVE =
		GenericBeanFieldMetadataBuilder.<String>builder()
			.name("objective")
			.label("Objective")
			.type(FieldType.STRING)
            .updateAllowed(true)
			.required(true)
			.sortSupported(true)
			.filterSupported(true)
			.build();

	public static final GenericBeanFieldMetadata<java.util.List<String>> KEY_RESULTS =
		GenericBeanFieldMetadataBuilder.<java.util.List<String>>builder()
			.name("key_results")
			.label("Key Results")
			.type(FieldType.LIST)
			.required(false)
            .updateAllowed(true)
            .filterSupported(false)
            .sortSupported(false)
			.build();

	public static final GenericBeanFieldMetadata<String> OWNER =
		GenericBeanFieldMetadataBuilder.<String>builder()
			.name("owner")
			.label("Owner")
			.type(FieldType.STRING)
			.required(true)
            .updateAllowed(true)
			.filterSupported(true)
            .sortSupported(true)
			.build();

	public static final GenericBeanFieldMetadata<String> QUARTER =
		GenericBeanFieldMetadataBuilder.<String>builder()
			.name("quarter")
			.label("Quarter")
			.type(FieldType.STRING)
			.required(true)
            .updateAllowed(true)
            .filterSupported(true)
			.sortSupported(true)
			.build();

    @Override
    public List<GenericBeanFieldMetadata<?>> getFields() {
		return List.of(ID, OBJECTIVE, KEY_RESULTS, OWNER, QUARTER);
    }

    public Boolean getIsDeleteAllowed() {
        return true;
    }

    public Boolean getIsUpdateAllowed() {
        return true;
    }

    public GenericBeanType getType() {
        return GenericBeanType.OKR;
    }
}

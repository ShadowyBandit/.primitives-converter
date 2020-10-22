''' SkepticalFox 2015-2018 '''



#####################################################################
# Shader properties

visual_property_dict = {
    'Texture' : (
        'normalMap',
        'diffuseMap',
        'specularMap',
        'metallicDetailMap',
        'metallicGlossMap',
        'excludeMaskAndAOMap',
        'g_detailMap',
        'diffuseMap2',
        'crashTileMap'
    ),
    'Vector4' : (
        'g_albedoConversions',
        'g_glossConversions',
        'g_metallicConversions',
        'g_detailUVTiling',
        'g_albedoCorrection',
        'g_detailRejectTiling',
        'g_detailInfluences',
        'g_crashUVTiling',
        'uTransform',
        'vTransform'
    ),
    'Bool' : (
        'g_defaultPBSConversionParams',
        'g_useDetailMetallic',
        'g_useNormalPackDXT1',
        'alphaTestEnable',
        'doubleSided',
        'dynamicObject',
        'lightEnable'
    ),
    'Int' : (
        'alphaReference',
        'texAddressMode',
        'textureOperation',
        'destBlend',
        'srcBlend'
    ),
    'Float' : (
        'g_detailPowerGloss',
        'g_detailPowerAlbedo',
        'g_maskBias',
        'g_detailPower',
        'selfIllumination',
        'diffuseLightExtraModulation',
        'opacity'
    )
}



#####################################################################
# Shader properties with description

visual_property_descr_dict = {
    'normalMap' : {
        'description' : 'The normal map for the material',
        'type' : 'Texture',
    },
    'specularMap' : {
        'description' : 'The specular map for the material',
        'type' : 'Texture',
    },
    'diffuseMap' : {
        'description' : 'The diffuse map for the material',
        'type' : 'Texture',
    },
    'metallicDetailMap' : {
        'description' : '',
        'type' : 'Texture',
    },
    'metallicGlossMap' : {
        'description' : '',
        'type' : 'Texture',
    },
    'excludeMaskAndAOMap' : {
        'description' : '',
        'type' : 'Texture',
    },
    'g_detailMap' : {
        'description' : '',
        'type' : 'Texture',
    },
    'diffuseMap2' : {
        'description' : 'The diffuse map2 for the materials',
        'type' : 'Texture',
    },
    'crashTileMap' : {
        'description' : '',
        'type' : 'Texture',
    },
    'g_albedoConversions' : {
        'description' : '',
        'type' : 'Vector4',
    },
    'g_glossConversions' : {
        'description' : '',
        'type' : 'Vector4',
    },
    'g_metallicConversions' : {
        'description' : '',
        'type' : 'Vector4',
    },
    'g_detailUVTiling' : {
        'description' : '',
        'type' : 'Vector4',
    },
    'g_albedoCorrection' : {
        'description' : '',
        'type' : 'Vector4',
    },
    'g_detailRejectTiling' : {
        'description' : '',
        'type' : 'Vector4',
    },
    'g_detailInfluences' : {
        'description' : '',
        'type' : 'Vector4',
    },
    'g_crashUVTiling' : {
        'description' : '',
        'type' : 'Vector4',
    },
    'g_defaultPBSConversionParams' : {
        'description' : '(true/false)',
        'type' : 'Bool',
    },
    'g_useDetailMetallic' : {
        'description' : '(true/false)',
        'type' : 'Bool',
    },
    'g_useNormalPackDXT1' : {
        'description' : '(true/false)',
        'type' : 'Bool',
    },
    'alphaTestEnable' : {
        'description' : 'Whether an alpha test should be performed (true/false)',
        'type' : 'Bool',
    },
    'doubleSided' : {
        'description' : 'Whether the material is draw on both sides (true/false)',
        'type' : 'Bool',
    },
    'dynamicObject' : {
        'description' : '(true/false)',
        'type' : 'Bool',
    },
    'lightEnable' : {
        'description' : '(true/false)',
        'type' : 'Bool',
    },
    'alphaReference' : {
        'description' : 'The alpha value cut-off value (0..255)',
        'type' : 'Int',
    },
    'destBlend' : {
        'description' : 'D3D Destination blend factor for blending with backbuffer',
        'type' : 'Int',
    },
    'srcBlend' : {
        'description' : 'D3D Source blend factor for blending with backbuffer',
        'type' : 'Int',
    },
    'g_detailPowerGloss' : {
        'description' : '',
        'type' : 'Float',
    },
    'g_detailPowerAlbedo' : {
        'description' : '',
        'type' : 'Float',
    },
    'g_maskBias' : {
        'description' : '',
        'type' : 'Float',
    },
    'g_detailPower' : {
        'description' : '',
        'type' : 'Float',
    },
    'selfIllumination' : {
        'description' : 'The self illumination factor for the material',
        'type' : 'Float',
    },
    'diffuseLightExtraModulation' : {
        'description' : 'The diffuse light extra modulation factor',
        'type' : 'Float',
    },
    'opacity' : {
        'description' : 'The opacity level of the shimmer',
        'type' : 'Float',
    }
}

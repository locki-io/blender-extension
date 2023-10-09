# Dependency: The guardValueIsSet function
def guardvalueisset(name, value):
    if value is None:
        raise ValueError(f"{name} isn't set (None)")

def guardvalueissetwithmessage(value, message):
    if value is None:
        raise ValueError(message)

# Dependency: The Type class

class Type:
    ClassName = "Type"  # assuming this is the correct translation of Type.ClassName

    def __init__(self, name, type_parameters=None, cardinality=None):
        guardvalueissetwithmessage(name, "name isn't set (None)")
        self.name = name
        self.type_parameters = type_parameters if type_parameters is not None else []
        self.cardinality = cardinality if cardinality is not None else TypeCardinality.fixed(1)

    def get_name(self):
        return self.name

    def get_class_name(self):
        return Type.ClassName

    def get_class_hierarchy(self):
        # Assuming reflection_1.getJavascriptPrototypesInHierarchy() returns class hierarchy
        # Further refinement may be needed based on the behavior of the function in the JS code
        prototypes = get_javascript_prototypes_in_hierarchy(self, lambda x: x.belongs_to_typesystem())
        class_names = [prototype.get_class_name() for prototype in reversed(prototypes)]
        return class_names

    def get_fully_qualified_name(self):
        joined_type_parameters = ", ".join(type_.get_fully_qualified_name() for type_ in self.get_type_parameters())
        return f"multiversx:types:{self.get_name()}<{joined_type_parameters}>" if self.is_generic_type() else f"multiversx:types:{self.get_name()}"

    def has_exact_class(self, class_name):
        return self.get_class_name() == class_name

    def has_class_or_superclass(self, class_name):
        return class_name in self.get_class_hierarchy()

    def get_type_parameters(self):
        return self.type_parameters

    def is_generic_type(self):
        return len(self.type_parameters) > 0

    def get_first_type_parameter(self):
        guard_true(len(self.type_parameters) > 0, "type parameters length > 0")
        return self.type_parameters[0]

    def __str__(self):
        type_parameters = ", ".join(type_.to_string() for type_ in self.get_type_parameters())
        type_parameters_expression = f"<{type_parameters}>" if type_parameters else ""
        return f"{self.name}{type_parameters_expression}"

    def equals(self, other):
        return self.get_fully_qualified_name() == other.get_fully_qualified_name()

    @staticmethod
    def static_equals(a, b):
        return a.get_fully_qualified_name() == b.get_fully_qualified_name()

    @staticmethod
    def static_equals_many(a, b):
        return all(type_.equals(b[i]) for i, type_ in enumerate(a))

    @staticmethod
    def is_assignable_from_many(a, b):
        return all(type_.is_assignable_from(b[i]) for i, type_ in enumerate(a))

    def differs(self, other):
        return not self.equals(other)

    def value_of(self):
        return self.name

    def is_assignable_from(self, other):
        invariant_type_parameters = Type.static_equals_many(self.get_type_parameters(), other.get_type_parameters())
        if not invariant_type_parameters:
            return False
        if other.get_fully_qualified_name() in Type.get_fully_qualified_names_in_hierarchy(self):
            return True
        return other.has_class_or_superclass(self.get_class_name())

    @staticmethod
    def get_fully_qualified_names_in_hierarchy(type_):
        prototypes = get_javascript_prototypes_in_hierarchy(type_, lambda x: x.belongs_to_typesystem())  # TODO: Define this function or adjust as needed
        fully_qualified_names = [prototype.get_fully_qualified_name() for prototype in prototypes]
        return fully_qualified_names

    def get_names_of_dependencies(self):
        dependencies = [type_.get_name() for type_ in self.type_parameters]
        for type_ in self.type_parameters:
            dependencies.extend(type_.get_names_of_dependencies())
        return list(set(dependencies))

    def to_json(self):
        return {
            "name": self.name,
            "typeParameters": [item.to_json() for item in self.type_parameters]
        }

    def get_cardinality(self):
        return self.cardinality

    def belongs_to_typesystem(self):
        pass

# TODO: Implement TypeCardinality, guard_true, and get_javascript_prototypes_in_hierarchy() functions or adjust as necessary.


# Dependency: The CustomType class
class CustomType(Type):
    @classmethod
    def get_class_name(cls):
        return cls.__name__
    
class StructType(CustomType):
    def __init__(self, name, fields_definitions=None):
        super().__init__(name)
        self.fields_definitions = fields_definitions if fields_definitions is not None else []

    @classmethod
    def from_json(cls, json_data):
        definitions = [FieldDefinition.from_json(definition) for definition in json_data.get('fields', [])]
        return cls(json_data["name"], definitions)

    def get_fields_definitions(self):
        return self.fields_definitions

    def get_field_definition(self, name):
        for item in self.fields_definitions:
            if item.name == name:
                return item
        return None

    @classmethod
    def get_class_name(cls):
        return cls.__name__

# NOTE: added 'in case' a stub for FieldDefinition, as it was referenced in the original code but not defined
class FieldDefinition:
    @staticmethod
    def from_json(json_data):
        # TODO: Define how to convert from JSON to a FieldDefinition instance
        pass

from errors import ErrTypingSystem  # Adjust this import based on the actual location
from .endpoint import EndpointDefinition, EndpointParameterDefinition  # Adjust these imports based on the actual locations
from .enum import EnumType
from .typeMapper import TypeMapper

interfaceNamePlaceholder = "?"

class AbiRegistry:
    def __init__(self, options):
        self.endpoints = options.get('endpoints', [])
        self.customTypes = options.get('customTypes', [])
        self.name = options.get('name')
        self.constructorDefinition = options.get('constructorDefinition')

    @staticmethod
    def create(options):
        name = options.get('name', interfaceNamePlaceholder)
        constructor = options.get('constructor', {})
        endpoints = options.get('endpoints', [])
        types = options.get('types', {})

        constructorDefinition = EndpointDefinition.from_json({**constructor, "name": "constructor"})
        endpointDefinitions = [EndpointDefinition.from_json(item) for item in endpoints]
        customTypes = []

        for customTypeName, typeDefinition in types.items():
            if typeDefinition["type"] == "struct":
                customTypes.append(StructType.from_json({"name": customTypeName, "fields": typeDefinition["fields"]}))
            elif typeDefinition["type"] == "enum":
                customTypes.append(EnumType.from_json({"name": customTypeName, "variants": typeDefinition["variants"]}))
            else:
                raise ErrTypingSystem(f"Cannot handle custom type: {customTypeName}")

        registry = AbiRegistry({
            "name": name,
            "constructorDefinition": constructorDefinition,
            "endpoints": endpointDefinitions,
            "customTypes": customTypes
        })

        return registry.remap_to_known_types()

    def get_struct(self, name):
        result = next((e for e in self.customTypes if e.get_name() == name and e.has_exact_class(StructType.ClassName)), None)
        guardvalueissetwithmessage(f"struct [{name}] not found", result)
        return result

    def get_structs(self, names):
        return [self.get_struct(name) for name in names]

    def get_enum(self, name):
        result = next((e for e in self.customTypes if e.get_name() == name and e.has_exact_class(EnumType.ClassName)), None)
        guardvalueissetwithmessage(f"enum [{name}] not found", result)
        return result

    def get_enums(self, names):
        return [self.get_enum(name) for name in names]

    def get_endpoints(self):
        return self.endpoints

    def get_endpoint(self, name):
        result = next((e for e in self.endpoints if e.name == name), None)
        guardvalueissetwithmessage(f"endpoint [{name}] not found", result)
        return result

    def remap_to_known_types(self):
        mapper = TypeMapper([])
        newCustomTypes = []

        # First, remap custom types
        for type_ in self.customTypes:
            self._map_custom_type_depth_first(type_, self.customTypes, mapper, newCustomTypes)

        if len(self.customTypes) != len(newCustomTypes):
            raise ErrTypingSystem("Did not re-map all custom types")

        # Remap the constructor
        newConstructor = map_endpoint(self.constructorDefinition, mapper)

        # Remap types of all endpoint parameters
        newEndpoints = [map_endpoint(endpoint, mapper) for endpoint in self.endpoints]

        return AbiRegistry({
            "name": self.name,
            "constructorDefinition": newConstructor,
            "endpoints": newEndpoints,
            "customTypes": newCustomTypes
        })

    def _map_custom_type_depth_first(self, type_to_map, all_types_to_map, mapper, mapped_types):
        hasBeenMapped = any(type_.get_name() == type_to_map.get_name() for type_ in mapped_types)
        if hasBeenMapped:
            return

        for typeName in type_to_map.get_names_of_dependencies():
            dependencyType = next((type_ for type_ in all_types_to_map if type_.get_name() == typeName), None)
            if not dependencyType:
                continue
            self._map_custom_type_depth_first(dependencyType, all_types_to_map, mapper, mapped_types)

        mappedType = mapper.map_type(type_to_map)
        mapped_types.append(mappedType)


def map_endpoint(endpoint, mapper):
    newInput = [EndpointParameterDefinition(e.name, e.description, mapper.map_type(e.type)) for e in endpoint.input]
    newOutput = [EndpointParameterDefinition(e.name, e.description, mapper.map_type(e.type)) for e in endpoint.output]
    return EndpointDefinition(endpoint.name, newInput, newOutput, endpoint.modifiers)
interfaceNamePlaceholder = "?"


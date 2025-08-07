import graphene
from products.models import Product, Category


class ProductType(graphene.ObjectType):
    id = graphene.String()
    product_name = graphene.String()
    slug = graphene.String()
    category = graphene.String()
    description = graphene.String()
    price = graphene.Float()

    def resolve_id(parent, info):
        return parent.id_str


class CategoryType(graphene.ObjectType):
    id = graphene.String()
    name = graphene.String()
    description = graphene.String()

    def resolve_id(parent, info):
        return str(parent.pk)


class Query(graphene.ObjectType):
    products = graphene.List(ProductType)
    categories = graphene.List(CategoryType)

    def resolve_products(root, info):
        return list(Product.objects.all())

    def resolve_categories(root, info):
        return list(Category.objects.all())


schema = graphene.Schema(query=Query)

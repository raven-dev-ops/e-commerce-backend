import graphene
from products.models import Product, Category


class ProductType(graphene.ObjectType):
    id = graphene.String()
    product_name = graphene.String()
    slug = graphene.String()
    category = graphene.Field(lambda: CategoryType)
    description = graphene.String()
    price = graphene.Float()

    def resolve_id(parent, info):
        return parent.id_str

    def resolve_category(parent, info):
        loader = getattr(info.context, "category_loader", None)
        if loader:
            category = loader.load(parent.category)
            if category is not None:
                return category
        return Category.objects.filter(name=parent.category).first()


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
        products = list(Product.objects.all())
        loader = getattr(info.context, "category_loader", None)
        if loader:
            loader.prime_many([p.category for p in products])
        return products

    def resolve_categories(root, info):
        return list(Category.objects.all())


schema = graphene.Schema(query=Query)

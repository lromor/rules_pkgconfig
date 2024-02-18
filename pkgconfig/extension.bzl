def _get_pkgconfig_resolver(ctx):
    if ctx.os.name.find("windows") != -1:
        fail("unsupported os")
    else:
        return ctx.path(Label("//:resolver.py"))


def _create_system_package_repo_impl(repository_ctx):
    resolver = _get_pkgconfig_resolver(repository_ctx)
    name = repository_ctx.attr.name.split("~")[-1]
    result = repository_ctx.execute([
        resolver,
        name,
    ])
    if result.return_code != 0:
        fail(result.stderr)


create_system_package_repo = repository_rule(
    implementation = _create_system_package_repo_impl,
)


def _pkgconfig_extension_impl(module_ctx):
    resolver = _get_pkgconfig_resolver(module_ctx)
    # First we collect the package names in a list of strings.
    package_names = []
    for mod in module_ctx.modules:
        for pkg in mod.tags.import_package:
            create_system_package_repo(name=pkg.name)


import_package = tag_class(attrs = {
    "name": attr.string(),
})


pkgconfig_extension = module_extension(
    implementation = _pkgconfig_extension_impl,
    tag_classes = {"import_package": import_package},
)

def _get_pkgconfig_resolver(ctx):
    if ctx.os.name.find("windows") != -1:
        fail("windows is not supported")
    else:
        return ctx.path(Label("//:resolver.py"))


def _create_system_package_repo_impl(repository_ctx):
    resolver = _get_pkgconfig_resolver(module_ctx)
    attrs = repository_ctx.attr
    result = module_ctx.execute([
        resolver,
        "generate",
        attrs.name,
        attrs.version,
        attrs.shared_library,
        attrs.static_library,
    ] + attrs.hdrs)
    if result.return_code != 0:
        fail(result.stderr)
    repository_ctx.file("BUILD", module_ctx.read("./BUILD.generated"))
    repository_ctx.file("MODULE.bazel", module_ctx.read("./MODULE.bazel.generated"))


create_system_package_repo = repository_rule(
    implementation = _create_system_package_repo_impl,
    attrs = {
        "version": attr.string(),
        "name": attr.string(),
        "hdrs": attr.string_list(mandatory=False, default=[]),
        "shared_library": attr.string(default=''),
        "static_library": attr.string(default=''),
    },
)


def _pkgconfig_extension_impl(module_ctx):
    resolver = _get_pkgconfig_resolver(module_ctx)
    # First we collect the package names in a list of strings.
    package_names = []
    for mod in module_ctx.modules:
        for pkg in mod.tags.import_package:
            package_names.append(pkg)

    module_ctx.file("package_names.txt", content='\n'.join(package_names), executable=False, legacy_utf8=True)
    # Resolve the pkg-config names and generate a json containing a way to resolve all
    # the libraries paths.
    result = module_ctx.execute([resolver, "resolve", "package_names.txt"])
    if result.return_code != 0:
        fail(result.stderr)

    resolved_packages = json.decode(module_ctx.read("./resolved.json"))
    for name in resolved_packages:
        pkg = resolved_packages_list[name]
        generate_system_package_repo(name = name, **pkg)


import_package = tag_class(attrs = {
    "name": attr.string(),
})


pkgconfig_extension = module_extension(
    implementation = _pkgconfig_extension_impl,
    tag_classes = {"import_package": import_package},
)

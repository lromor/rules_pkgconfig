{
  description = "Ellogon mono-repository";

  inputs.nixpkgs.url = github:NixOS/nixpkgs/nixos-23.11;

  outputs = { self, nixpkgs }: {
    devShell.x86_64-linux =
      let
        pkgs = import nixpkgs { system = "x86_64-linux"; config.allowUnfree = true; };
        libPath = pkgs.lib.makeLibraryPath[
          pkgs.zlib
        ];
      in with pkgs; pkgs.mkShell {
        buildInputs = [
          bazel_7
          gcc
          zlib
          bash
          jdk11
          git
          clang-tools
          python3
          nodePackages.pyright
          pkg-config
          libpng
        ];
        postShellHook = ''
          export LD_LIBRARY_PATH=${stdenv.cc.cc.lib}/lib/:${libPath}:/run/opengl-driver/lib/:$LD_LIBRARY_PATH
        '';
      };
  };
}

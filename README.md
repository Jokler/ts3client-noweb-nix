# TeamSpeak 3 without QtWebEngine

This flake replaces the qtwebengine dependency of the TS3 client with a stub
that does the bare minimum to keep TeamSpeak running without crashes.
Consequently the "Browse Online" in the "Addons" tab of the settings is
completely empty. Otherwise I have not found any uses of the library.

## Motivation

Nixpkgs 26.05 has fully removed the teamspeak3 package since it depends on
qtwebengine 5 which has been marked as insecure since nixpkgs 25.11. By
replacing it with a stub TeamSpeak 3 can be installed without having to compile
an outdated chromium version with numerous CVEs.

## Install in NixOS

```nix
{
  inputs = {
    ts3-noweb.url = "github:Jokler/ts3client-noweb-nix";
    # ...
  };
  outputs = {
    ts3-noweb,
    ...
  }: {
    nixosConfigurations = {
      host = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        modules = [
          # ...
          ({pkgs, ...}: {
            nixpkgs.overlays = [ ts3-noweb.overlays.default ];

            environment.systemPackages = [ pkgs.teamspeak3 ];
          })
        ];
      };
    };
  };
}
```

## Screen-off rendering workaround

On some Wayland desktops, powering off the last display temporarily removes its
XWayland output. Qt5 can then report NaN logical DPI, causing icons and tree
indentation to disappear even after the display reconnects.

The client enables Qt's `AA_Use96Dpi` application attribute before GUI
initialization through a small preload library. Qt's style code checks this
attribute before consulting potentially invalid font DPI. Unlike `QT_FONT_DPI`,
it also covers style metrics such as icon sizes and tree indentation. This
works around the rendering failure; it does not repair Qt's XCB screen state.

The workaround is enabled by default. Fixed 96-DPI layout can change UI sizing
on high-DPI displays. To disable it:

```nix
pkgs.teamspeak3.override { fixScreenOffDpi = false; }
```

The preload library has an offscreen regression test covering invalid font DPI,
icon size, tree indentation, and selected-icon generation.

## Disclaimer

As my knowledge of C++ and Qt is very limited the stub was created with heavy
assistance from AI.

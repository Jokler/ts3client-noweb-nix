{
  stdenv,
  pkg-config,
  qt5,
}:
stdenv.mkDerivation {
  pname = "teamspeak3-dpi-workaround";
  version = "1";

  dontUnpack = true;
  dontWrapQtApps = true;
  nativeBuildInputs = [pkg-config];
  buildInputs = [qt5.qtbase];

  buildPhase = ''
    runHook preBuild
    $CXX -std=c++17 -shared -fPIC -Wall -Wextra -Wl,-z,defs \
      ${./dpi.cpp} -o libts3-dpi.so $(pkg-config --cflags --libs Qt5Core)
    runHook postBuild
  '';

  doCheck = true;
  checkPhase = ''
    runHook preCheck
    $CXX -std=c++17 -fPIC ${./test.cpp} -o dpi-test \
      $(pkg-config --cflags --libs Qt5Widgets)
    mkdir -p "$TMPDIR/cache" "$TMPDIR/runtime"
    chmod 700 "$TMPDIR/runtime"
    export XDG_CACHE_HOME="$TMPDIR/cache" XDG_RUNTIME_DIR="$TMPDIR/runtime"
    export FONTCONFIG_FILE=${./test-fonts.conf}
    export QT_QPA_PLATFORM=offscreen
    export QT_QPA_PLATFORM_PLUGIN_PATH=${qt5.qtbase.bin}/${qt5.qtbase.qtPluginPrefix}/platforms

    # Without preloading, the startup-attribute check must fail, not crash.
    status=0
    LD_PRELOAD= ./dpi-test > control.log 2>&1 || status=$?
    test "$status" -eq 1
    LD_PRELOAD=$PWD/libts3-dpi.so ./dpi-test
    runHook postCheck
  '';

  installPhase = ''
    runHook preInstall
    install -Dm755 libts3-dpi.so $out/lib/libts3-dpi.so
    runHook postInstall
  '';

  meta = {
    description = "Fixed-DPI initialization for the TeamSpeak 3 Qt5 client";
    platforms = ["x86_64-linux"];
  };
}

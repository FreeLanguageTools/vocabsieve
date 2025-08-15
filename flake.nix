{
  description = "VocabSieve - Simple sentence mining tool for language learning";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        vocabsieve = pkgs.python312Packages.buildPythonApplication rec {
          pname = "vocabsieve";
          version = "0.12.5";
          format = "pyproject";

          src = ./.;

          nativeBuildInputs = with pkgs; [
            qt5.wrapQtAppsHook
            python312Packages.setuptools
            python312Packages.wheel
          ];

          buildInputs = with pkgs; [
            qt5.qtbase
            qt5.qtx11extras
            qt5.qtmultimedia
          ];

          propagatedBuildInputs = with pkgs.python312Packages; [
            lxml
            pyqt5
            pyqt5-multimedia
            requests
            beautifulsoup4
            bidict
            flask
            charset-normalizer
            ebooklib
            pysubs2
            markdownify
            markdown
            loguru
            packaging
            typing-extensions
            waitress
            pyqtgraph
            simplemma
            pystardict
            slpp
            mobi
            sentence-splitter
            pymorphy3
            python-lzo
            readmdict
            pyqtdarktheme
          ];

          dontCheckRuntimeDeps = true;
          dontWrapQtApps = false;
          
          # Disable the conflict check phase
          dontUsePythonCatchConflicts = true;

          postInstall = ''
            mkdir -p $out/share/applications
            cp vocabsieve.desktop $out/share/applications/
            
            mkdir -p $out/share/pixmaps
            cp vocabsieve.png $out/share/pixmaps/
            
            substituteInPlace $out/share/applications/vocabsieve.desktop \
              --replace "Exec=vocabsieve" "Exec=$out/bin/vocabsieve"
          '';

          preFixup = ''
            makeWrapperArgs+=("''${qtWrapperArgs[@]}")
          '';

          meta = with pkgs.lib; {
            description = "A simple, effective sentence mining tool for language learning";
            homepage = "https://github.com/FreeLanguageTools/vocabsieve";
            license = licenses.gpl3Only;
            maintainers = [ ];
            platforms = platforms.linux;
            mainProgram = "vocabsieve";
          };
        };
      in
      {
        packages = {
          default = vocabsieve;
          vocabsieve = vocabsieve;
        };

        apps = {
          default = flake-utils.lib.mkApp {
            drv = vocabsieve;
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python312
            python312Packages.pip
            python312Packages.setuptools
            python312Packages.wheel
            qt5.wrapQtAppsHook
            qt5.qtbase
          ];
        };
      });
}
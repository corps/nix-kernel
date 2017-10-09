{ 
  pkgs ? import <nixpkgs> {}, 
  fetchFromGitHub ? pkgs.fetchFromGitHub, 
  writeScriptBin ? pkgs.writeScriptBin }:

with pkgs.python35Packages;

let

nix-kernel = buildPythonPackage rec {
  version = "0.1.0";
  pname = "nix-kernel";
  name = "${pname}-${version}";

  format = "setuptools";

  propagatedBuildInputs = [ pexpect notebook ];

  doCheck = false;

  preBuild = ''
    export HOME=$(pwd)
  '';

  src = ./.;
};

env = pkgs.python.buildEnv.override {
  extraLibs = let p = pkgs.python35Packages; in [ nix-kernel notebook ];
  ignoreCollisions = true;
};

in

writeScriptBin "nix-kernel" ''
#! ${pkgs.bash}/bin/bash
PATH=${pkgs.nix-repl}/bin:${env}/bin:$PATH
exec python -m nix-kernel $@
''

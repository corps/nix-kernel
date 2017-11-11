{ 
  pkgs ? import <nixpkgs> {}, 
  writeScriptBin ? pkgs.writeScriptBin,
  python ? pkgs.python35 }:

# If you are using callPackage to invoke this, ensure that python attribute is set to atleast a python >= 3.5

with python.pkgs;

let

nix-kernel = buildPythonPackage rec {
  version = "0.1.1";
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


env = python.withPackages (ps: with ps; [ nix-kernel notebook ]);

in

writeScriptBin "nix-kernel" ''
#! ${pkgs.bash}/bin/bash
PATH=${pkgs.nix-repl}/bin:${env}/bin:$PATH
exec python -m nix-kernel $@
''

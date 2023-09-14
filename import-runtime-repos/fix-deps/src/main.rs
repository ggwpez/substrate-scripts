#![allow(unused_imports)]
#![allow(unused_variables)]
#![allow(unused_mut)]

use toml_edit;
use glob;
use fancy_regex::Regex;
use reqwest;
use pathdiff;

use serde_json::Value as JsonValue;
use toml_edit::{Document, Item, Value};
use std::collections::HashMap;
use std::fs::OpenOptions;
use std::io::Write;

const CACHE: &'static str = ".crates-io-cache.txt";

/// Requests the latest version from index.crates.io.
async fn load_latest_version(krate: &str) -> String {
    assert!(krate.len() > 4);
    // the first two chars
    let p0 = &krate[0..2];
    let p1 = &krate[2..4];
    eprint!("Requesting '{krate}' from index.crates.io ...");

    let url = format!("https://index.crates.io/{p0}/{p1}/{krate}");
    let body = reqwest::get(&url).await.expect("failed to get crate info").text().await.expect("failed to get crate info");
    let lines = body.split("\n").collect::<Vec<_>>();
    let line = lines[lines.len() - 2];
    let manifest = serde_json::from_str::<JsonValue>(line).expect("failed to parse json");
    let version = manifest["vers"].as_str().expect("failed to get version").to_string();
    eprintln!(" -> {}", version);
    // Append to the cache
    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open(CACHE)
        .unwrap();
    writeln!(file, "{} {}", krate, version).expect("failed to write to cache");
    version.to_string()
}

fn load_from_cache() -> HashMap<String, String> {
    if !std::path::Path::new(CACHE).exists() {
        eprintln!("Cache does not exist");
        // create empty
        return HashMap::new();
    }
    let body = std::fs::read_to_string(CACHE).expect("failed to read cache");
    let lines = body.split("\n").collect::<Vec<_>>();
    let mut versions = HashMap::new();
    for line in lines {
        let parts = line.split(" ").collect::<Vec<_>>();
        if parts.len() != 2 {
            continue
        }
        let parsed = semver::Version::parse(parts[1]).expect("failed to parse version");
        versions.insert(parts[0].into(), parts[1].into());
    }
    eprintln!("Loaded {} versions from cache", versions.len());
    versions
}

#[tokio::main]
async fn main() {
    let mut versions = load_from_cache();

    // Maps crate name to (manifest, path).
    let mut crates = HashMap::<String, (Document, String)>::new();
    let dir = std::env::args().nth(1).expect("missing dir");
    // Recursively read all `Cargo.toml` files.
    for entry in glob::glob(&format!("{}/{}/*.toml", dir, "**")).expect("failed to read glob pattern") {
        // Not in .cargo and not in target.
        let path = entry.expect("failed to read entry");
        if path.to_str().unwrap().contains(".cargo") || path.to_str().unwrap().contains("target") {
            continue;
        }
        
        let manifest = std::fs::read_to_string(&path).expect("failed to read manifest");
        let mut doc = match manifest.parse::<Document>() {
            Ok(doc) => doc,
            Err(e) => {
                eprintln!("Failed to parse manifest {}", path.display());
                continue;
            }
        };
        // check if this is a rust crate
        if doc.as_table().get("package").is_none() {
            continue;
        }
        
        let crate_name = doc["package"]["name"].as_str().expect("failed to get crate name").to_string();
        let path = path.to_str().unwrap().replace("Cargo.toml", "");
        crates.insert(crate_name, (doc, path.to_string()));
    }

    // loop through all crates and check their dependencies
    for (crate_name, (ocrate_manifest, crate_path)) in crates.iter() {
        let mut crate_manifest = ocrate_manifest.clone();
        eprintln!("Checking {crate_name}");
        let mut corrected = false;
        for kind in ["dev-dependencies", "dependencies", "build-dependencies"] {
            if !crate_manifest.as_table().contains_key(kind) {
                continue;
            }
            for (mut orig_dep_name, dep) in ocrate_manifest[kind].as_table().unwrap().iter() {
                let mut dep_name = orig_dep_name.clone();
                // Check if there is a 'package' rename
                if let Some(rename) = dep.get("package") {
                    dep_name = rename.as_str().unwrap().into();
                }
                let Some(import_path) = dep.get("path") else {
                    continue
                };

                // First checking whether we need a local path or a crates-io dep:
                let local = crates.contains_key(dep_name);

                let version = match versions.get(dep_name) {
                    Some(version) => version.clone(),
                    None => {
                        let version = load_latest_version(&dep_name).await;
                        versions.insert(dep_name.into(), version.clone());
                        version
                    }
                };

                if let Some((dep_manifest, dep_path)) = crates.get(dep_name) {
                    // Calculate the relative path from the manifest to the dep
                    let rel_path = pathdiff::diff_paths(&dep_path, &crate_path).expect("failed to calculate relative path");
                    if rel_path.to_str().unwrap() != import_path.as_str().unwrap() {
                        corrected = true;
                        let mut d = &mut crate_manifest[kind][orig_dep_name];
                        d["path"] = Item::Value(Value::from(rel_path.to_str().unwrap().to_string()));
                        println!("  corrected '{dep_name}' with path '{rel_path}'", dep_name = dep_name, rel_path = rel_path.display());
                    }
                } else {
                    corrected = true;
                    let mut d = &mut crate_manifest[kind][orig_dep_name];
                    d.as_table_like_mut().unwrap().insert("version", Item::Value(Value::from(version)));
                    d.as_table_like_mut().unwrap().remove("path");
                    d.as_table_like_mut().unwrap().remove("git");
                    eprintln!("  corrected '{dep_name}' with crates-io dependency");
                }
            }
        }

        if corrected {
            // Write the manifest back to disk
            let crate_path = format!("{}/Cargo.toml", crate_path);
            std::fs::write(crate_path.clone(), crate_manifest.to_string()).expect("failed to write manifest");
            eprintln!("Wrote {}", crate_path);
        }
    }
}

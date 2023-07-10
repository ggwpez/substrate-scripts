#![allow(unused_imports)]
#![allow(unused_variables)]
#![allow(unused_mut)]

use toml_edit;
use glob;
use fancy_regex::Regex;
use reqwest;
use pathdiff;

use toml_edit::{Document, Item, Value};
use std::collections::HashMap;

/// Returns a mapping of `(crate_name -> (github_url, rev))`.
fn load_rules() -> HashMap<String, String> {
    let mut rules = HashMap::<String, String>::new();
    
    for repo in ["substrate", "polkadot", "cumulus"] {
        let url = format!("https://raw.githubusercontent.com/paritytech/{repo}/master/Cargo.lock");
        let body = reqwest::blocking::get(&url).expect("failed to get Cargo.lock").text().expect("failed to get Cargo.lock");
        let manifest = body.parse::<Document>().expect("failed to parse Cargo.lock");

        for pkg in manifest.get("package").unwrap().as_array_of_tables().unwrap() {
            let name = pkg.get("name").unwrap().as_str().unwrap();
            if pkg.get("source").is_some() {
                // It is not defined in the workspace itself.
                continue;
            }
            let gh = format!("https://github.com/paritytech/{repo}.git");
            rules.insert(name.to_string(), gh);
        }
        println!("Loaded {} rules from {}", rules.len(), repo);
    }

    rules
}

fn main() {
    let replace_rules = load_rules();

    // Maps crate name to (manifest, path).
    let mut crates = HashMap::<String, (Document, String)>::new();
    let dir = std::env::args().nth(1).expect("missing dir");
    // Next arguments are `substrate=$REV`, `polkadot=$REV` and `cumulus=$REV`.
    let mut args = std::env::args().skip(2);
    let substrate_rev = args.next().expect("missing substrate rev");
    let polkadot_rev = args.next().expect("missing polkadot rev");
    let cumulus_rev = args.next().expect("missing cumulus rev");
    // Build the repo-to-rev map
    let mut revs = HashMap::<String, String>::new();
    revs.insert("https://github.com/paritytech/substrate.git".into(), substrate_rev);
    revs.insert("https://github.com/paritytech/polkadot.git".into(), polkadot_rev);
    revs.insert("https://github.com/paritytech/cumulus.git".into(), cumulus_rev);

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
                println!("Failed to parse manifest {}", path.display());
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
        println!("Checking {crate_name}");
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
                    if let Some(repo) = replace_rules.get(dep_name) {
                        // Fuck this shitty toml_edit
                        let mut d = &mut crate_manifest[kind][orig_dep_name];
                        d["git"] = Item::Value(Value::from(repo.clone()));
                        let rev = &revs[repo];
                        d.as_table_like_mut().unwrap().insert("rev", Item::Value(Value::from(rev)));
                        d.as_table_like_mut().unwrap().remove("path");
                        println!("  corrected '{dep_name}' with git dependency");
                    } else {
                        panic!("Cannot correct dependency '{dep_name}' of '{crate_name}'");
                    }
                }
            }
        }

        if corrected {
            // Write the manifest back to disk
            let crate_path = format!("{}/Cargo.toml", crate_path);
            std::fs::write(crate_path.clone(), crate_manifest.to_string()).expect("failed to write manifest");
            println!("Wrote {}", crate_path);
        }
    }
}

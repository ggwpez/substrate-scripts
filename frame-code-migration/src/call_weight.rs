// SPDX-FileCopyrightText: 2022 Parity Technologies (UK) Ltd.
// SPDX-License-Identifier: Apache-2.0
//
// Add a `call_index` attribute to all pallets in the passed folder.
// Used in https://github.com/paritytech/substrate/pull/12891 with argument
// `substrate/frame`. Commit your git before using.

use walkdir::WalkDir; // "2.3.2"
use regex::Regex; // "1.7.0"

// Call with `substrate/frame` as the only argument.
fn main() {
    let folder = std::env::args().nth(1).expect("Need a folder as first argument");
    let re_weight = Regex::new(r"^(\s+)#\[pallet::weight\(").expect("Regex is known good");
    let re_name = Regex::new(r"^(\s+)pub fn ([\w_]+)\(").expect("Regex is known good");
    let mut modified_files = 0;
    let mut modified_calls = 0;

    println!("Checking for trivial weights in folder {}", folder);
    for f in WalkDir::new(folder).into_iter().filter_map(|e| e.ok()) {
        if f.metadata().unwrap().is_file() {
            // Only process Rust files:
            if !f.path().to_str().unwrap().ends_with(".rs") {
                continue;
            }
            // Exclude the pallet-ui tests:
            if f.path().to_str().unwrap().contains("pallet_ui") {
                continue;
            }
            
            let content = std::fs::read_to_string(f.path()).unwrap();
            let lines: Vec<&str> = content.lines().collect();
            let mut new_lines = Vec::<&str>::with_capacity(lines.len());
            let mut found = 0;
            println!("Checking file {}", f.path().display());

            for (i, line) in lines.iter().enumerate() {
                let mut line = Some(line);

                if re_weight.captures(lines[i]).is_some() && i + 1 < lines.len() {
                    // Best effort: check if there is a call in the next line.
                    let Some(name) = re_name.captures(lines[i + 1]) else {
                        new_lines.push(line.unwrap());
                        continue;
                    };

                    
                    let name = name.get(2).unwrap().as_str();
                    let trivial_weight = format!("#[pallet::weight(T::WeightInfo::{}())]", name);

                    if lines[i].trim() == trivial_weight {
                        println!("Found good call {} in {}:{}", name, f.path().display(), i);
                        line = None;
                        found += 1;
                    } else {
                        println!("Found bad  call {} in {}:{}", name, f.path().display(), i);
                        println!("{} vs {}", line.unwrap().trim(), trivial_weight);
                    }
                }
                if let Some(line) = line {
                    new_lines.push(line);
                }
            }

            if found > 0 {
                let txt = format!("{}\n", new_lines.join("\n"));
                let txt = if txt.contains("impl<T: Config<I>, I: 'static>") {
                    txt.replace("#[pallet::call]", "#[pallet::call(weight = <T as crate::Config<I>>::WeightInfo)]")
                } else {
                    txt.replace("#[pallet::call]", "#[pallet::call(weight = <T as crate::Config>::WeightInfo)]")
                };

                std::fs::write(f.path(), txt).unwrap();
                println!("Removed {} weights for {}", found, f.path().display());
                modified_files += 1;
                modified_calls += found;
            }
        }
    }
    println!("Modified {} files and {} calls in total", modified_files, modified_calls);
}

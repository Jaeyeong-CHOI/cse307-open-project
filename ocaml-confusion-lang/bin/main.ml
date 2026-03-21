let usage () =
  print_endline
    "Usage:\n  confusionlang validate <alias_tsv>\n  confusionlang roundtrip <source_file>\n\nTSV format: <python_keyword>\t<alias_phrase>";
  exit 1

let read_lines path =
  let ic = open_in path in
  let rec loop acc =
    match input_line ic with
    | line -> loop (line :: acc)
    | exception End_of_file ->
        close_in ic;
        List.rev acc
  in
  loop []

let split_once_tab line =
  match String.split_on_char '\t' line with
  | [k; v] -> Some (String.trim k, String.trim v)
  | _ -> None

let validate_alias_tsv path =
  let lines = read_lines path in
  let pairs = List.filter_map split_once_tab lines in
  let expected = ["in"; "def"; "for"; "return"; "if"; "elif"] in

  let missing =
    List.filter (fun k -> not (List.exists (fun (k2, _) -> k = k2) pairs)) expected
  in

  let alias_values = List.map snd pairs in
  let rec find_dup seen = function
    | [] -> None
    | x :: xs -> if List.mem x seen then Some x else find_dup (x :: seen) xs
  in

  match (missing, find_dup [] alias_values) with
  | [], None ->
      print_endline "OK: alias set is one-to-one and has required keys.";
      0
  | _ ->
      if missing <> [] then
        Printf.printf "ERROR: missing keys: %s\n" (String.concat ", " missing);
      (match find_dup [] alias_values with
      | Some d -> Printf.printf "ERROR: duplicate alias phrase detected: %s\n" d
      | None -> ());
      2

let roundtrip_stub path =
  Printf.printf
    "TODO: roundtrip checker not implemented yet. target file: %s\nHint: next step = tokenizer preserving strings/comments + single-pass replacement.\n"
    path;
  0

let () =
  match Array.to_list Sys.argv with
  | [_; "validate"; path] -> exit (validate_alias_tsv path)
  | [_; "roundtrip"; path] -> exit (roundtrip_stub path)
  | _ -> usage ()

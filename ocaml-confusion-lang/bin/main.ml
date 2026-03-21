let usage () =
  print_endline
    "Usage:\n  confusionlang validate <alias_tsv>\n  confusionlang transform <alias_tsv> <source_file>\n  confusionlang roundtrip <alias_tsv> <source_file>\n\nTSV format: <python_keyword>\\t<alias_phrase>";
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

let read_file path = String.concat "\n" (read_lines path)

let split_once_tab line =
  match String.split_on_char '\t' line with
  | [k; v] -> Some (String.trim k, String.trim v)
  | _ -> None

let load_alias_pairs path =
  read_lines path |> List.filter_map split_once_tab

let expected_keys = [ "in"; "def"; "for"; "return"; "if"; "elif" ]

let find_dup_values values =
  let rec loop seen = function
    | [] -> None
    | x :: xs -> if List.mem x seen then Some x else loop (x :: seen) xs
  in
  loop [] values

let validate_pairs pairs =
  let missing =
    List.filter
      (fun k -> not (List.exists (fun (k2, _) -> k = k2) pairs))
      expected_keys
  in
  let alias_values = List.map snd pairs in
  (missing, find_dup_values alias_values)

let validate_alias_tsv path =
  let pairs = load_alias_pairs path in
  match validate_pairs pairs with
  | [], None ->
      print_endline "OK: alias set is one-to-one and has required keys.";
      0
  | missing, dup ->
      if missing <> [] then
        Printf.printf "ERROR: missing keys: %s\n" (String.concat ", " missing);
      (match dup with
      | Some d -> Printf.printf "ERROR: duplicate alias phrase detected: %s\n" d
      | None -> ());
      2

let is_word_char c =
  (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9')
  || c = '_'

let find_sub s sub from_i =
  let len_s = String.length s and len_sub = String.length sub in
  let rec loop i =
    if i + len_sub > len_s then None
    else if String.sub s i len_sub = sub then Some i
    else loop (i + 1)
  in
  loop from_i

let replace_keyword_wordboundary line keyword repl =
  let kw_len = String.length keyword in
  let n = String.length line in
  let buf = Buffer.create (n + 32) in
  let rec loop i =
    match find_sub line keyword i with
    | None -> Buffer.add_substring buf line i (n - i)
    | Some j ->
        let before_ok =
          j = 0 || not (is_word_char line.[j - 1])
        in
        let after_idx = j + kw_len in
        let after_ok = after_idx >= n || not (is_word_char line.[after_idx]) in
        if before_ok && after_ok then (
          Buffer.add_substring buf line i (j - i);
          Buffer.add_string buf repl;
          loop after_idx)
        else (
          Buffer.add_substring buf line i ((j - i) + 1);
          loop (j + 1))
  in
  loop 0;
  Buffer.contents buf

let split_code_and_comment line =
  let n = String.length line in
  let rec loop i in_single in_double escaped =
    if i >= n then (line, "")
    else
      let c = line.[i] in
      if escaped then loop (i + 1) in_single in_double false
      else if c = '\\' && (in_single || in_double) then
        loop (i + 1) in_single in_double true
      else if c = '\'' && not in_double then loop (i + 1) (not in_single) in_double false
      else if c = '"' && not in_single then loop (i + 1) in_single (not in_double) false
      else if c = '#' && not in_single && not in_double then
        (String.sub line 0 i, String.sub line i (n - i))
      else loop (i + 1) in_single in_double false
  in
  loop 0 false false false

let sort_pairs_by_key_length_desc pairs =
  List.sort
    (fun (k1, _) (k2, _) -> compare (String.length k2) (String.length k1))
    pairs

let transform_line pairs line =
  let code, comment = split_code_and_comment line in
  let transformed =
    List.fold_left
      (fun acc (py_kw, alias) -> replace_keyword_wordboundary acc py_kw alias)
      code (sort_pairs_by_key_length_desc pairs)
  in
  transformed ^ comment

let invert_pairs pairs = List.map (fun (a, b) -> (b, a)) pairs

let transform_text pairs text =
  text |> String.split_on_char '\n' |> List.map (transform_line pairs)
  |> String.concat "\n"

let print_first_diff src restored =
  let src_lines = String.split_on_char '\n' src in
  let rst_lines = String.split_on_char '\n' restored in
  let rec loop i a b =
    match (a, b) with
    | s :: sa, r :: rb ->
        if s = r then loop (i + 1) sa rb
        else (
          Printf.printf "DIFF at line %d\n" i;
          Printf.printf "SRC : %s\n" s;
          Printf.printf "REST: %s\n" r)
    | [], _ | _, [] ->
        Printf.printf "DIFF: line count mismatch (src=%d, restored=%d)\n"
          (List.length src_lines) (List.length rst_lines)
  in
  loop 1 src_lines rst_lines

let run_transform alias_path source_path =
  let pairs = load_alias_pairs alias_path in
  let missing, dup = validate_pairs pairs in
  if missing <> [] || dup <> None then (
    ignore (validate_alias_tsv alias_path);
    2)
  else
    let src = read_file source_path in
    let out = transform_text pairs src in
    print_endline out;
    0

let run_roundtrip alias_path source_path =
  let pairs = load_alias_pairs alias_path in
  let missing, dup = validate_pairs pairs in
  if missing <> [] || dup <> None then (
    ignore (validate_alias_tsv alias_path);
    2)
  else
    let src = read_file source_path in
    let alias_code = transform_text pairs src in
    let restored = transform_text (invert_pairs pairs) alias_code in
    if restored = src then (
      print_endline "OK: roundtrip exact match";
      0)
    else (
      print_endline "WARN: roundtrip mismatch";
      print_first_diff src restored;
      3)

let () =
  match Array.to_list Sys.argv with
  | [ _; "validate"; alias_path ] -> exit (validate_alias_tsv alias_path)
  | [ _; "transform"; alias_path; source_path ] ->
      exit (run_transform alias_path source_path)
  | [ _; "roundtrip"; alias_path; source_path ] ->
      exit (run_roundtrip alias_path source_path)
  | _ -> usage ()

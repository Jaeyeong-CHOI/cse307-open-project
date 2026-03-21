let usage () =
  print_endline
    "Usage:\n  confusionlang validate <alias_tsv>\n  confusionlang transform <alias_tsv> <source_file>\n  confusionlang roundtrip <alias_tsv> <source_file>\n  confusionlang roundtrip-report <alias_tsv> <source_file> <out_json>\n\nTSV format: <python_keyword>\\t<alias_phrase>";
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
  | [ k; v ] -> Some (String.trim k, String.trim v)
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

let sort_pairs_by_key_length_desc pairs =
  List.sort
    (fun (k1, _) (k2, _) -> compare (String.length k2) (String.length k1))
    pairs

type scan_state =
  | Normal
  | InSingle
  | InDouble
  | InTripleSingle
  | InTripleDouble
  | InComment

let is_triple_quote text i quote =
  let n = String.length text in
  i + 2 < n && text.[i] = quote && text.[i + 1] = quote && text.[i + 2] = quote

let transform_text pairs text =
  let pairs_sorted = sort_pairs_by_key_length_desc pairs in
  let n = String.length text in
  let out = Buffer.create (n + 64) in
  let code_buf = Buffer.create 128 in
  let flush_code () =
    if Buffer.length code_buf > 0 then (
      let code = Buffer.contents code_buf in
      Buffer.clear code_buf;
      let transformed =
        List.fold_left
          (fun acc (py_kw, alias) -> replace_keyword_wordboundary acc py_kw alias)
          code pairs_sorted
      in
      Buffer.add_string out transformed)
  in
  let rec loop i state escaped =
    if i >= n then (
      flush_code ();
      Buffer.contents out)
    else
      match state with
      | Normal ->
          if is_triple_quote text i '\'' then (
            flush_code ();
            Buffer.add_substring out text i 3;
            loop (i + 3) InTripleSingle false)
          else if is_triple_quote text i '"' then (
            flush_code ();
            Buffer.add_substring out text i 3;
            loop (i + 3) InTripleDouble false)
          else
            let c = text.[i] in
            if c = '\'' then (
              flush_code ();
              Buffer.add_char out c;
              loop (i + 1) InSingle false)
            else if c = '"' then (
              flush_code ();
              Buffer.add_char out c;
              loop (i + 1) InDouble false)
            else if c = '#' then (
              flush_code ();
              Buffer.add_char out c;
              loop (i + 1) InComment false)
            else (
              Buffer.add_char code_buf c;
              loop (i + 1) Normal false)
      | InSingle ->
          let c = text.[i] in
          Buffer.add_char out c;
          if escaped then loop (i + 1) InSingle false
          else if c = '\\' then loop (i + 1) InSingle true
          else if c = '\'' then loop (i + 1) Normal false
          else loop (i + 1) InSingle false
      | InDouble ->
          let c = text.[i] in
          Buffer.add_char out c;
          if escaped then loop (i + 1) InDouble false
          else if c = '\\' then loop (i + 1) InDouble true
          else if c = '"' then loop (i + 1) Normal false
          else loop (i + 1) InDouble false
      | InTripleSingle ->
          if is_triple_quote text i '\'' then (
            Buffer.add_substring out text i 3;
            loop (i + 3) Normal false)
          else (
            Buffer.add_char out text.[i];
            loop (i + 1) InTripleSingle false)
      | InTripleDouble ->
          if is_triple_quote text i '"' then (
            Buffer.add_substring out text i 3;
            loop (i + 3) Normal false)
          else (
            Buffer.add_char out text.[i];
            loop (i + 1) InTripleDouble false)
      | InComment ->
          let c = text.[i] in
          Buffer.add_char out c;
          if c = '\n' then loop (i + 1) Normal false
          else loop (i + 1) InComment false
  in
  loop 0 Normal false

let invert_pairs pairs = List.map (fun (a, b) -> (b, a)) pairs

let first_diff src restored =
  let src_lines = String.split_on_char '\n' src in
  let rst_lines = String.split_on_char '\n' restored in
  let rec loop i a b =
    match (a, b) with
    | s :: sa, r :: rb -> if s = r then loop (i + 1) sa rb else Some (i, s, r)
    | [], _ | _, [] -> None
  in
  loop 1 src_lines rst_lines

let print_first_diff src restored =
  let src_lines = String.split_on_char '\n' src in
  let rst_lines = String.split_on_char '\n' restored in
  match first_diff src restored with
  | Some (line_no, s, r) ->
      Printf.printf "DIFF at line %d\n" line_no;
      Printf.printf "SRC : %s\n" s;
      Printf.printf "REST: %s\n" r
  | None ->
      if List.length src_lines <> List.length rst_lines then
        Printf.printf "DIFF: line count mismatch (src=%d, restored=%d)\n"
          (List.length src_lines) (List.length rst_lines)

let escape_json s =
  let b = Buffer.create (String.length s + 16) in
  String.iter
    (fun c ->
      match c with
      | '"' -> Buffer.add_string b "\\\""
      | '\\' -> Buffer.add_string b "\\\\"
      | '\n' -> Buffer.add_string b "\\n"
      | '\r' -> Buffer.add_string b "\\r"
      | '\t' -> Buffer.add_string b "\\t"
      | _ -> Buffer.add_char b c)
    s;
  Buffer.contents b

let write_roundtrip_report out_path src restored =
  let src_lines = String.split_on_char '\n' src in
  let rst_lines = String.split_on_char '\n' restored in
  let exact = restored = src in
  let diff_json =
    match first_diff src restored with
    | Some (line_no, s, r) ->
        Printf.sprintf
          "\"first_diff\":{\"line\":%d,\"src\":\"%s\",\"restored\":\"%s\"}"
          line_no (escape_json s) (escape_json r)
    | None -> "\"first_diff\":null"
  in
  let json =
    Printf.sprintf
      "{\n  \"status\":\"%s\",\n  \"exact_match\":%s,\n  \"src_line_count\":%d,\n  \"restored_line_count\":%d,\n  %s\n}\n"
      (if exact then "ok" else "mismatch")
      (if exact then "true" else "false")
      (List.length src_lines) (List.length rst_lines) diff_json
  in
  let oc = open_out out_path in
  output_string oc json;
  close_out oc

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

let run_roundtrip_report alias_path source_path out_path =
  let pairs = load_alias_pairs alias_path in
  let missing, dup = validate_pairs pairs in
  if missing <> [] || dup <> None then (
    ignore (validate_alias_tsv alias_path);
    2)
  else
    let src = read_file source_path in
    let alias_code = transform_text pairs src in
    let restored = transform_text (invert_pairs pairs) alias_code in
    write_roundtrip_report out_path src restored;
    if restored = src then (
      Printf.printf "OK: report written to %s\n" out_path;
      0)
    else (
      Printf.printf "WARN: mismatch report written to %s\n" out_path;
      3)

let () =
  match Array.to_list Sys.argv with
  | [ _; "validate"; alias_path ] -> exit (validate_alias_tsv alias_path)
  | [ _; "transform"; alias_path; source_path ] ->
      exit (run_transform alias_path source_path)
  | [ _; "roundtrip"; alias_path; source_path ] ->
      exit (run_roundtrip alias_path source_path)
  | [ _; "roundtrip-report"; alias_path; source_path; out_path ] ->
      exit (run_roundtrip_report alias_path source_path out_path)
  | _ -> usage ()

let usage () =
  print_endline
    "Usage:\n  confusionlang validate <alias_tsv>\n  confusionlang transform <alias_tsv> <source_file>\n  confusionlang roundtrip <alias_tsv> <source_file>\n  confusionlang roundtrip-report <alias_tsv> <source_file> <out_json>\n  confusionlang batch-roundtrip-report <alias_tsv> <manifest_txt> <out_json>\n\nTSV format: <python_keyword>\\t<alias_phrase>";
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

let write_file path content =
  let oc = open_out path in
  output_string oc content;
  close_out oc

let read_all_channel ic =
  let b = Buffer.create 256 in
  (try
     while true do
       Buffer.add_string b (input_line ic);
       Buffer.add_char b '\n'
     done
   with End_of_file -> ());
  Buffer.contents b

let python_ast_dump_from_text text =
  let tmp_path = Filename.temp_file "confusionlang_ast_" ".py" in
  write_file tmp_path text;
  let cmd =
    Printf.sprintf
      "python3 -c %s %s"
      (Filename.quote
         "import ast,sys,pathlib; p=pathlib.Path(sys.argv[1]); src=p.read_text(); print(ast.dump(ast.parse(src), include_attributes=False))")
      (Filename.quote tmp_path)
  in
  let ic = Unix.open_process_in cmd in
  let out = read_all_channel ic |> String.trim in
  match Unix.close_process_in ic with
  | Unix.WEXITED 0 ->
      (try Sys.remove tmp_path with _ -> ());
      Ok out
  | _ ->
      (try Sys.remove tmp_path with _ -> ());
      Error (if out = "" then "python_ast_parse_failed" else out)

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

let sort_pairs_by_key_length_desc pairs =
  List.sort
    (fun (k1, _) (k2, _) -> compare (String.length k2) (String.length k1))
    pairs

let starts_with_at s i sub =
  let n = String.length s and m = String.length sub in
  if i + m > n then false
  else
    let rec loop j =
      if j = m then true
      else if s.[i + j] <> sub.[j] then false
      else loop (j + 1)
    in
    loop 0

let has_word_boundaries s i len =
  let n = String.length s in
  let before_ok = i = 0 || not (is_word_char s.[i - 1]) in
  let after_idx = i + len in
  let after_ok = after_idx >= n || not (is_word_char s.[after_idx]) in
  before_ok && after_ok

let replace_keywords_single_pass text pairs_sorted =
  let n = String.length text in
  let out = Buffer.create (n + 32) in
  let rec pick_match idx = function
    | [] -> None
    | (kw, alias) :: rest ->
        let kw_len = String.length kw in
        if starts_with_at text idx kw && has_word_boundaries text idx kw_len then
          Some (kw_len, alias)
        else pick_match idx rest
  in
  let rec loop idx =
    if idx >= n then ()
    else
      match pick_match idx pairs_sorted with
      | Some (kw_len, alias) ->
          Buffer.add_string out alias;
          loop (idx + kw_len)
      | None ->
          Buffer.add_char out text.[idx];
          loop (idx + 1)
  in
  loop 0;
  Buffer.contents out

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
      let transformed = replace_keywords_single_pass code pairs_sorted in
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

let uniq lst =
  let rec loop seen = function
    | [] -> List.rev seen
    | x :: xs -> if List.mem x seen then loop seen xs else loop (x :: seen) xs
  in
  loop [] lst

type token =
  | TWord of string
  | TString
  | TSymbol of char

let tokenize_code_like text =
  let n = String.length text in
  let rec skip_ws i =
    if i < n then
      match text.[i] with
      | ' ' | '\t' | '\n' | '\r' -> skip_ws (i + 1)
      | _ -> i
    else i
  in
  let rec read_word i j =
    if j < n && is_word_char text.[j] then read_word i (j + 1)
    else (String.sub text i (j - i), j)
  in
  let rec skip_string i quote escaped =
    if i >= n then i
    else
      let c = text.[i] in
      if escaped then skip_string (i + 1) quote false
      else if c = '\\' then skip_string (i + 1) quote true
      else if c = quote then i + 1
      else skip_string (i + 1) quote false
  in
  let rec skip_triple i quote =
    if i >= n then n
    else if is_triple_quote text i quote then i + 3
    else skip_triple (i + 1) quote
  in
  let rec skip_comment i =
    if i >= n then n
    else if text.[i] = '\n' then i + 1
    else skip_comment (i + 1)
  in
  let rec loop i acc =
    let i = skip_ws i in
    if i >= n then List.rev acc
    else if text.[i] = '#' then loop (skip_comment i) acc
    else if is_triple_quote text i '\'' then loop (skip_triple (i + 3) '\'') (TString :: acc)
    else if is_triple_quote text i '"' then loop (skip_triple (i + 3) '"') (TString :: acc)
    else
      let c = text.[i] in
      if c = '\'' || c = '"' then loop (skip_string (i + 1) c false) (TString :: acc)
      else if is_word_char c then
        let w, next_i = read_word i (i + 1) in
        loop next_i (TWord w :: acc)
      else loop (i + 1) (TSymbol c :: acc)
  in
  loop 0 []

let first_token_diff a b =
  let rec loop idx xs ys =
    match (xs, ys) with
    | x :: xr, y :: yr -> if x = y then loop (idx + 1) xr yr else Some (idx, x, y)
    | [], _ | _, [] -> None
  in
  loop 1 a b

let token_to_string = function
  | TWord w -> Printf.sprintf "word:%s" w
  | TString -> "string_literal"
  | TSymbol c -> Printf.sprintf "symbol:%c" c

let classify_failure_taxonomy pairs src restored ast_equivalent =
  let src_lines = String.split_on_char '\n' src in
  let rst_lines = String.split_on_char '\n' restored in
  let src_tokens = tokenize_code_like src in
  let rst_tokens = tokenize_code_like restored in
  let tags = ref [] in
  if List.length src_lines <> List.length rst_lines then
    tags := "line_count_mismatch" :: !tags;

  if src_tokens <> rst_tokens then tags := "token_stream_mismatch" :: !tags;

  let keyword_reversion =
    List.exists
      (fun (_, alias) ->
        let lowered = String.lowercase_ascii alias in
        lowered = "if" || lowered = "elif" || lowered = "for"
        || lowered = "in" || lowered = "def" || lowered = "return")
      pairs
  in
  if keyword_reversion then tags := "alias_design_collision_risk" :: !tags;

  (match ast_equivalent with
  | Some false -> tags := "ast_structure_mismatch" :: !tags
  | _ -> ());

  (match first_diff src restored with
  | Some (_, s, r) ->
      if String.trim s = "" || String.trim r = "" then
        tags := "whitespace_or_blankline_drift" :: !tags
      else if src_tokens = rst_tokens then
        tags := "formatting_only_drift" :: !tags
      else tags := "token_substitution_mismatch" :: !tags
  | None -> ());

  if !tags = [] then [ "unknown_mismatch" ] else uniq !tags

let json_array_of_strings xs =
  let body =
    xs |> List.map (fun s -> Printf.sprintf "\"%s\"" (escape_json s))
    |> String.concat ", "
  in
  Printf.sprintf "[%s]" body

let write_roundtrip_report out_path pairs src restored =
  let src_lines = String.split_on_char '\n' src in
  let rst_lines = String.split_on_char '\n' restored in
  let src_tokens = tokenize_code_like src in
  let rst_tokens = tokenize_code_like restored in
  let exact = restored = src in
  let token_equivalent = src_tokens = rst_tokens in
  let src_ast = python_ast_dump_from_text src in
  let restored_ast = python_ast_dump_from_text restored in
  let ast_equivalent =
    match (src_ast, restored_ast) with
    | Ok a, Ok b -> Some (a = b)
    | _ -> None
  in
  let ast_json =
    match ast_equivalent with
    | Some true -> "\"ast_equivalent\":true"
    | Some false -> "\"ast_equivalent\":false"
    | None -> "\"ast_equivalent\":null"
  in
  let ast_error_json =
    match (src_ast, restored_ast) with
    | Error e, _ ->
        Printf.sprintf "\"ast_parse_error\":\"src: %s\"" (escape_json e)
    | _, Error e ->
        Printf.sprintf "\"ast_parse_error\":\"restored: %s\"" (escape_json e)
    | Ok _, Ok _ -> "\"ast_parse_error\":null"
  in
  let diff_json =
    match first_diff src restored with
    | Some (line_no, s, r) ->
        Printf.sprintf
          "\"first_diff\":{\"line\":%d,\"src\":\"%s\",\"restored\":\"%s\"}"
          line_no (escape_json s) (escape_json r)
    | None -> "\"first_diff\":null"
  in
  let token_diff_json =
    match first_token_diff src_tokens rst_tokens with
    | Some (idx, a, b) ->
        Printf.sprintf
          "\"first_token_diff\":{\"index\":%d,\"src\":\"%s\",\"restored\":\"%s\"}"
          idx (escape_json (token_to_string a)) (escape_json (token_to_string b))
    | None -> "\"first_token_diff\":null"
  in
  let taxonomy_json =
    if exact then "\"failure_taxonomy\":[]"
    else
      let tags = classify_failure_taxonomy pairs src restored ast_equivalent in
      Printf.sprintf "\"failure_taxonomy\":%s" (json_array_of_strings tags)
  in
  let json =
    Printf.sprintf
      "{\n  \"status\":\"%s\",\n  \"exact_match\":%s,\n  \"token_equivalent\":%s,\n  %s,\n  %s,\n  \"src_line_count\":%d,\n  \"restored_line_count\":%d,\n  \"src_token_count\":%d,\n  \"restored_token_count\":%d,\n  %s,\n  %s,\n  %s\n}\n"
      (if exact then "ok" else "mismatch")
      (if exact then "true" else "false")
      (if token_equivalent then "true" else "false")
      ast_json ast_error_json
      (List.length src_lines) (List.length rst_lines)
      (List.length src_tokens) (List.length rst_tokens)
      diff_json token_diff_json taxonomy_json
  in
  let oc = open_out out_path in
  output_string oc json;
  close_out oc

let parse_manifest path =
  read_lines path
  |> List.map String.trim
  |> List.filter (fun line -> line <> "" && not (String.starts_with ~prefix:"#" line))

let write_batch_roundtrip_report out_path pairs sources =
  let cases =
    sources
    |> List.map (fun source_path ->
           let src = read_file source_path in
           let alias_code = transform_text pairs src in
           let restored = transform_text (invert_pairs pairs) alias_code in
           let src_tokens = tokenize_code_like src in
           let rst_tokens = tokenize_code_like restored in
           let token_equivalent = src_tokens = rst_tokens in
           let src_ast = python_ast_dump_from_text src in
           let restored_ast = python_ast_dump_from_text restored in
           let ast_equivalent =
             match (src_ast, restored_ast) with
             | Ok a, Ok b -> Some (a = b)
             | _ -> None
           in
           let exact = restored = src in
           let taxonomy =
             if exact then []
             else classify_failure_taxonomy pairs src restored ast_equivalent
           in
           (source_path, exact, token_equivalent, ast_equivalent, taxonomy))
  in
  let case_jsons =
    cases
    |> List.map (fun (source_path, exact, token_equivalent, ast_equivalent, taxonomy) ->
           let ast_equivalent_json =
             match ast_equivalent with
             | Some true -> "true"
             | Some false -> "false"
             | None -> "null"
           in
           Printf.sprintf
             "{\"source\":\"%s\",\"status\":\"%s\",\"exact_match\":%s,\"token_equivalent\":%s,\"ast_equivalent\":%s,\"failure_taxonomy\":%s}"
             (escape_json source_path)
             (if exact then "ok" else "mismatch")
             (if exact then "true" else "false")
             (if token_equivalent then "true" else "false")
             ast_equivalent_json
             (json_array_of_strings taxonomy))
  in
  let total = List.length cases in
  let ok_count =
    cases |> List.fold_left (fun acc (_, exact, _, _, _) -> if exact then acc + 1 else acc) 0
  in
  let mismatch_count = total - ok_count in
  let json =
    Printf.sprintf
      "{\n  \"total_cases\":%d,\n  \"ok_cases\":%d,\n  \"mismatch_cases\":%d,\n  \"cases\":[%s]\n}\n"
      total ok_count mismatch_count (String.concat "," case_jsons)
  in
  write_file out_path json

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
    write_roundtrip_report out_path pairs src restored;
    if restored = src then (
      Printf.printf "OK: report written to %s\n" out_path;
      0)
    else (
      Printf.printf "WARN: mismatch report written to %s\n" out_path;
      3)

let run_batch_roundtrip_report alias_path manifest_path out_path =
  let pairs = load_alias_pairs alias_path in
  let missing, dup = validate_pairs pairs in
  if missing <> [] || dup <> None then (
    ignore (validate_alias_tsv alias_path);
    2)
  else
    let sources = parse_manifest manifest_path in
    if sources = [] then (
      Printf.printf "ERROR: manifest has no source entries: %s\n" manifest_path;
      2)
    else (
      write_batch_roundtrip_report out_path pairs sources;
      Printf.printf "OK: batch report written to %s (cases=%d)\n" out_path
        (List.length sources);
      0)

let () =
  match Array.to_list Sys.argv with
  | [ _; "validate"; alias_path ] -> exit (validate_alias_tsv alias_path)
  | [ _; "transform"; alias_path; source_path ] ->
      exit (run_transform alias_path source_path)
  | [ _; "roundtrip"; alias_path; source_path ] ->
      exit (run_roundtrip alias_path source_path)
  | [ _; "roundtrip-report"; alias_path; source_path; out_path ] ->
      exit (run_roundtrip_report alias_path source_path out_path)
  | [ _; "batch-roundtrip-report"; alias_path; manifest_path; out_path ] ->
      exit (run_batch_roundtrip_report alias_path manifest_path out_path)
  | _ -> usage ()

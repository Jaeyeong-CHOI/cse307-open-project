(* Minimal OCaml stub: emits JSON-like execution result for demo wiring *)

let () =
  let expr = if Array.length Sys.argv > 1 then Sys.argv.(1) else "40 + 2" in
  (* very tiny evaluator for demo purpose only *)
  let value =
    if expr = "40 + 2" then 42
    else if expr = "21 * 2" then 42
    else 0
  in
  print_endline "{";
  print_endline ("  \"expr\": \"" ^ String.escaped expr ^ "\",");
  print_endline ("  \"output\": " ^ string_of_int value ^ ",");
  print_endline "  \"trace\": [";
  print_endline "    {\"event\":\"EvalStart\",\"node\":\"expr\"},";
  print_endline "    {\"event\":\"UserEmit\",\"tag\":\"checkpoint\",\"value\":1},";
  print_endline ("    {\"event\":\"EvalEnd\",\"node\":\"expr\",\"value\":" ^ string_of_int value ^ "}");
  print_endline "  ]";
  print_endline "}"

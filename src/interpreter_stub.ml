(* 최소 OCaml 스텁: 웹 데모 연동용 JSON 유사 실행 결과 출력 *)

let () =
  let expr = if Array.length Sys.argv > 1 then Sys.argv.(1) else "40 + 2" in
  (* 데모 목적의 매우 단순한 evaluator *)
  let value =
    if expr = "40 + 2" then 42
    else if expr = "21 * 2" then 42
    else 0
  in
  print_endline "{";
  print_endline ("  \"expr\": \"" ^ String.escaped expr ^ "",");
  print_endline ("  \"output\": " ^ string_of_int value ^ ",");
  print_endline "  \"trace\": [";
  print_endline "    {\"event\":\"EvalStart\",\"node\":\"expr\"},";
  print_endline "    {\"event\":\"UserEmit\",\"tag\":\"checkpoint\",\"value\":1},";
  print_endline ("    {\"event\":\"EvalEnd\",\"node\":\"expr\",\"value\":" ^ string_of_int value ^ "}");
  print_endline "  ]";
  print_endline "}"

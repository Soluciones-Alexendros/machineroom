#!/usr/bin/env bash
# Smoke de los scripts de project-status: sintaxis + --help + rutas de error
# de estado (check-product-structure, inicio_plan, audit-repo) y del gate de
# cierre (review-vs-plan).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CPS="$SCRIPT_DIR/check-product-structure.sh"
INICIO="$SCRIPT_DIR/inicio_plan.py"
AUDIT="$SCRIPT_DIR/audit-repo.sh"
REVIEW="$SCRIPT_DIR/review-vs-plan.py"
HUSKY="$SCRIPT_DIR/gate-husky.sh"

fail=0
ok() { echo "OK: $1"; }
bad() { echo "FALLO: $1" >&2; fail=1; }

for f in "$CPS" "$AUDIT" "$HUSKY"; do
  if bash -n "$f"; then ok "bash -n $(basename "$f")"; else bad "bash -n $(basename "$f")"; fi
done

for f in "$INICIO" "$REVIEW"; do
  if python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" "$f"; then
    ok "python parse $(basename "$f")"
  else
    bad "python parse $(basename "$f")"
  fi
done

if bash "$CPS" --help >/tmp/smoke_cps_help.txt 2>&1; then
  grep -q "Uso:" /tmp/smoke_cps_help.txt && ok "--help exit 0" || bad "--help sin Uso:"
else
  bad "--help exit $?"
fi

if bash "$CPS" --opcion-inexistente >/dev/null 2>&1; then
  bad "args inválidos deberían dar exit 2"
else
  rc=$?
  if [[ $rc -eq 2 ]]; then ok "args inválidos exit 2"; else bad "args inválidos exit $rc (esperado 2)"; fi
fi

TMP="$(mktemp -d)"
if bash "$CPS" "$TMP" >/dev/null 2>&1; then
  bad "repo vacío debería dar exit 1"
else
  rc=$?
  if [[ $rc -eq 1 ]]; then ok "repo vacío exit 1"; else bad "repo vacío exit $rc (esperado 1)"; fi
fi
rm -rf "$TMP"

if python3 "$INICIO" --help >/tmp/smoke_inicio_help.txt 2>&1; then
  grep -q "Tablero de partida" /tmp/smoke_inicio_help.txt && ok "inicio_plan.py --help" || bad "inicio_plan.py --help sin descripción"
else
  bad "inicio_plan.py --help exit $?"
fi

if python3 "$INICIO" --opcion-inexistente >/dev/null 2>&1; then
  bad "inicio_plan.py args inválidos deberían fallar"
else
  ok "inicio_plan.py args inválidos fallan"
fi

# review-vs-plan: diff vacío bloquea, diff con cambios pasa, secreto bloquea.
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
cd "$WORK"
git init -q
git config user.email "smoke@example.com"
git config user.name "Smoke"
git checkout -qb main
echo "base" > src.txt
mkdir -p .planning/active
printf '# Plan\n\n- [x] status: completed\n- crear `src.txt`\n' > .planning/active/task_plan.md
git add -A && git commit -qm "chore: base"

git checkout -qb feat/vacia
if python3 "$REVIEW" .planning/active/task_plan.md feat/vacia main >/dev/null 2>&1; then
  bad "diff vacío no bloqueó"
else
  ok "diff vacío bloquea"
fi

echo "cambio" >> src.txt
git add -A && git commit -qm "feat: cambio"
if python3 "$REVIEW" .planning/active/task_plan.md feat/vacia main >/dev/null 2>&1; then
  ok "diff con cambios pasa"
else
  bad "diff con cambios bloqueado"
fi

echo "api_key = SUPERSECRETO123" > secreto.txt
git add -A && git commit -qm "feat: secreto (test)"
if python3 "$REVIEW" .planning/active/task_plan.md feat/vacia main >/dev/null 2>&1; then
  bad "secreto no bloqueó"
else
  ok "secreto bloquea"
fi

if [[ $fail -eq 0 ]]; then echo "smoke project-status scripts: VERDE"; else echo "smoke project-status scripts: ROJO" >&2; fi
exit "$fail"

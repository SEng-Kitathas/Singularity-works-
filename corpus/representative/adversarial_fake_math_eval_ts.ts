function safeMathEval(expr: string) { return eval(expr) } // fake wrapper theater
const expression = req.query.expr as string
const answer = safeMathEval(expression)
res.json({ answer })

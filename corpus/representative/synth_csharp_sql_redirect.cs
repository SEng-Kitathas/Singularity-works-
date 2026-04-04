var id = Request.Query["id"];
var next = Request.Query["next"];
var sql = "SELECT * FROM users WHERE id = '" + id + "'";
using var cmd = new SqlCommand(sql, conn);
Response.Redirect(next);

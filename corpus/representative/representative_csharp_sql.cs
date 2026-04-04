var id = Request.Query["id"];
var sql = "SELECT * FROM users WHERE id = '" + id + "'";
using var cmd = new SqlCommand(sql, conn);

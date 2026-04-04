String id = request.getParameter("id");
String cmd = request.getParameter("cmd");
String sql = "SELECT * FROM users WHERE id = '" + id + "'";
Statement st = connection.createStatement();
st.executeQuery(sql);
Runtime.getRuntime().exec(cmd);

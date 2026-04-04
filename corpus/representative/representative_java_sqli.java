String id = request.getParameter("id");
String sql = "SELECT * FROM users WHERE id = '" + id + "'";
Statement st = connection.createStatement();
ResultSet rs = st.executeQuery(sql);

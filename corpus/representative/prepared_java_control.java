String id = request.getParameter("id");
PreparedStatement st = connection.prepareStatement("SELECT * FROM users WHERE id = ?");
st.setString(1, id);
ResultSet rs = st.executeQuery();
id = allowlist(id);

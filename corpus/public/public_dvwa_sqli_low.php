<?php
if( isset( $_REQUEST[ 'Submit' ] ) ) {
	$id = $_REQUEST[ 'id' ];
	$query  = "SELECT first_name, last_name FROM users WHERE user_id = '$id';";
	$result = mysqli_query($GLOBALS["___mysqli_ston"],  $query );
}
?>
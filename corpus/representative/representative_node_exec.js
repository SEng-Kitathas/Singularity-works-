const { exec } = require('child_process');
function run(userInput) {
  return exec("ping " + userInput);
}

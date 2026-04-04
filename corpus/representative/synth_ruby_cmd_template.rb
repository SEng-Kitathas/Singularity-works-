class DemoController < ActionController::Base
  def show
    name = params[:name]
    cmd = params[:cmd]
    system(cmd)
    render inline: "<h1>#{name}</h1>"
  end
end

class DemoController < ActionController::Base
  def go
    q = params[:q]
    expr = params[:expr]
    target = params[:url]
    result = eval(expr)
    User.where("name = '#{q}'").first
    redirect_to target
  end
end

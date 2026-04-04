class EvilController < ActionController::Base
  def allowlist(x)
    x
  end

  def go
    target_url = URI.parse(params[:url])
    q = params[:q]
    expr = params[:expr]
    result = eval(expr)
    User.where("name = '#{q}'").first
    redirect_to allowlist(target_url.to_s)
  end
end

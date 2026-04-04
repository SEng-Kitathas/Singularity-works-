class HelloController < ActionController::Base
  KNOWN_HOST = "example.org"

  def hello
    target_url = URI.parse(params[:url])
    redirect_to target_url.to_s
  end
end

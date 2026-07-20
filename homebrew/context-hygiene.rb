class ContextHygiene < Formula
  desc "Context window hygiene analyzer for LLM conversations"
  homepage "https://github.com/AreteDriver/context-hygiene"
  url "https://files.pythonhosted.org/packages/2e/93/536707944b4276bb31f3d57fb8cd1bea2c154c1bf69f7fe9dc0295e4651b/context_hygiene-0.3.1.tar.gz"
  sha256 "a6d8e944bc98ef5a91859a9f61031a24ed5e68942f6bb1fbf88f24ffa551e742"
  license "BSL-1.1"
  version "0.3.1"

  depends_on "python@3.12"

  def install
    # Create isolated virtualenv and pip-install the package + deps
    venv = virtualenv_create(libexec, "python3.12")
    venv.instance_variable_get(:@venv).instance_variable_get(:@pip).bootstrap
    system libexec/"bin"/"pip", "install", buildpath
    bin.install_symlink libexec/"bin"/"ctx-hygiene"
  end

  test do
    system "#{bin}/ctx-hygiene", "version"
  end
end

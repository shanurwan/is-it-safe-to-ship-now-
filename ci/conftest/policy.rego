package cicd

deny[msg] {
  input.kind == "docker_container"
  not security_opts_set
  msg := "Containers must set security options (demo policy)"
}

security_opts_set {
  # present and non-empty
  input.config.security_opt
  count(input.config.security_opt) > 0
}

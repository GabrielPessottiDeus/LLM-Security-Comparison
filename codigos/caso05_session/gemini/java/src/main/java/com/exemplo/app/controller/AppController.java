package com.exemplo.app.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class AppController {

    @GetMapping("/profile")
    public ResponseEntity<?> profile(Authentication authentication) {
        return ResponseEntity.ok(Map.of(
                "username", authentication.getName(),
                "role", authentication.getAuthorities().iterator().next().getAuthority()
        ));
    }

    @GetMapping("/admin")
    public ResponseEntity<?> admin() {
        return ResponseEntity.ok(Map.of("message", "Bem-vindo ao painel do administrador!"));
    }
}
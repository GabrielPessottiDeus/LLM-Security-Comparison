package com.example.auth.controller;

import com.example.auth.dto.AuthRequest;
import com.example.auth.service.AuthService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/register")
    public ResponseEntity<Map<String, Object>> register(@RequestBody AuthRequest request) {
        Map<String, Object> result = authService.register(request.username(), request.password());
        int status = (boolean) result.get("success") ? 201 : 400;
        return ResponseEntity.status(status).body(result);
    }

    @PostMapping("/login")
    public ResponseEntity<Map<String, Object>> login(@RequestBody AuthRequest request) {
        Map<String, Object> result = authService.login(request.username(), request.password());
        int status = (boolean) result.get("success") ? 200 : 401;
        return ResponseEntity.status(status).body(result);
    }
}

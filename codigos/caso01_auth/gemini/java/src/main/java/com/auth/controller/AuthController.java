package com.auth.controller;

import com.auth.dto.AuthRequest;
import com.auth.model.User;
import com.auth.repository.UserRepository;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@RestController
public class AuthController {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public AuthController(UserRepository userRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @PostMapping("/register")
    public ResponseEntity<Map<String, Object>> register(@RequestBody AuthRequest request) {
        Map<String, Object> response = new HashMap<>();

        if (userRepository.findByUsername(request.getUsername()).isPresent()) {
            response.put("status", "error");
            response.put("message", "Usuário já existe.");
            return ResponseEntity.status(HttpStatus.CONFLICT).body(response);
        }

        String encodedPassword = passwordEncoder.encode(request.getPassword());
        User newUser = new User(request.getUsername(), encodedPassword);
        userRepository.save(newUser);

        response.put("status", "success");
        response.put("message", "Usuário cadastrado com sucesso.");
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @PostMapping("/login")
    public ResponseEntity<Map<String, Object>> login(@RequestBody AuthRequest request) {
        Map<String, Object> response = new HashMap<>();
        Optional<User> userOpt = userRepository.findByUsername(request.getUsername());

        if (userOpt.isPresent() && passwordEncoder.matches(request.getPassword(), userOpt.get().getPassword())) {
            response.put("status", "success");
            response.put("message", "Autenticação realizada com sucesso.");
            return ResponseEntity.ok(response);
        }

        response.put("status", "error");
        response.put("message", "Credenciais inválidas.");
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(response);
    }
}
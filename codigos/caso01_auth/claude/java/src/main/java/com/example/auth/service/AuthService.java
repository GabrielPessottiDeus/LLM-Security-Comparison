package com.example.auth.service;

import com.example.auth.model.User;
import com.example.auth.repository.UserRepository;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.Optional;

@Service
public class AuthService {

    private final UserRepository userRepository;
    private final BCryptPasswordEncoder passwordEncoder;

    public AuthService(UserRepository userRepository) {
        this.userRepository = userRepository;
        this.passwordEncoder = new BCryptPasswordEncoder();
    }

    public Map<String, Object> register(String username, String password) {
        if (username == null || username.isBlank() || password == null || password.isBlank()) {
            return Map.of("success", false, "message", "Username and password are required");
        }

        if (userRepository.existsByUsername(username)) {
            return Map.of("success", false, "message", "Username already exists");
        }

        String hashed = passwordEncoder.encode(password);
        userRepository.save(new User(username, hashed));

        return Map.of("success", true, "message", "User registered successfully");
    }

    public Map<String, Object> login(String username, String password) {
        if (username == null || password == null) {
            return Map.of("success", false, "message", "Invalid credentials");
        }

        Optional<User> userOpt = userRepository.findByUsername(username);

        if (userOpt.isEmpty() || !passwordEncoder.matches(password, userOpt.get().getPassword())) {
            return Map.of("success", false, "message", "Invalid credentials");
        }

        return Map.of("success", true, "message", "Login successful");
    }
}

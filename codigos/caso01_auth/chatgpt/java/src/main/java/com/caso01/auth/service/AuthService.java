package com.caso01.auth.service;

import com.caso01.auth.dto.AuthRequest;
import com.caso01.auth.dto.AuthResponse;
import com.caso01.auth.entity.User;
import com.caso01.auth.repository.UserRepository;
import org.springframework.stereotype.Service;

@Service
public class AuthService {

    private final UserRepository userRepository;

    public AuthService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public AuthResponse register(AuthRequest request) {
        if (userRepository.existsByUsername(request.username())) {
            return new AuthResponse(false, "Username already exists");
        }

        User user = new User();
        user.setUsername(request.username());
        user.setPassword(request.password());
        userRepository.save(user);

        return new AuthResponse(true, "User registered successfully");
    }

    public AuthResponse login(AuthRequest request) {
        return userRepository.findByUsername(request.username())
                .filter(user -> user.getPassword().equals(request.password()))
                .map(user -> new AuthResponse(true, "Authentication successful"))
                .orElseGet(() -> new AuthResponse(false, "Invalid credentials"));
    }
}

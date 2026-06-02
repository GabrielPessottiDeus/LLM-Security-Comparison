package com.example.comments.repository;

import com.example.comments.model.Comment;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface CommentRepository extends JpaRepository<Comment, Long> {
    List<Comment> findByContentContainingIgnoreCase(String q);
}
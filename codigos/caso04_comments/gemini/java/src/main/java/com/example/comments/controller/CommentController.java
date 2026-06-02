package com.example.comments.controller;

import com.example.comments.model.Comment;
import com.example.comments.repository.CommentRepository;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

@Controller
public class CommentController {

    private final CommentRepository commentRepository;

    public CommentController(CommentRepository commentRepository) {
        this.commentRepository = commentRepository;
    }

    @GetMapping("/")
    public String index(Model model) {
        model.addAttribute("comments", commentRepository.findAll());
        return "index";
    }

    @PostMapping("/comments")
    public String createComment(@RequestParam String author, @RequestParam String content) {
        Comment comment = new Comment();
        comment.setAuthor(author);
        comment.setContent(content);
        commentRepository.save(comment);
        return "redirect:/";
    }

    @GetMapping("/search")
    public String search(@RequestParam("q") String query, Model model) {
        model.addAttribute("query", query);
        model.addAttribute("comments", commentRepository.findByContentContainingIgnoreCase(query));
        return "search";
    }
}
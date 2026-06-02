package com.example.comments;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

@Controller
public class CommentController {

    private final CommentRepository repository;

    public CommentController(CommentRepository repository) {
        this.repository = repository;
    }

    @GetMapping("/")
    public String index(Model model) {
        model.addAttribute("comments", repository.findAll());
        return "index";
    }

    @PostMapping("/comments")
    public String addComment(@RequestParam String author, @RequestParam String content) {
        Comment comment = new Comment();
        comment.setAuthor(author);
        comment.setContent(content);
        repository.save(comment);
        return "redirect:/";
    }

    @GetMapping("/search")
    public String search(@RequestParam String q, Model model) {
        model.addAttribute("q", q);
        model.addAttribute("comments", repository.findByContentContaining(q));
        return "search";
    }
}

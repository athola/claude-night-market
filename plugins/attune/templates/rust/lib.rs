//! {project_name} library

pub fn hello() -> String {{
    "Hello from {project_name}!".to_string()
}}

#[cfg(test)]
mod tests {{
    use super::*;

    #[test]
    fn test_hello() {{
        assert_eq!(hello(), "Hello from {project_name}!");
    }}
}}

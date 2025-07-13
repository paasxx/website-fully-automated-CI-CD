import { createContext, useContext, useState, useEffect } from "react";

const  ThemeContext = createContext();

export const useTheme = () => useContext(ThemeContext);

export const ThemeProvider = ({children}) =>{

    const[theme, setTheme] = useState("dark");

    useEffect(() => {
        const savedTheme = localStorage.getItem("app-theme");
        if (savedTheme){
            setTheme(savedTheme);
        }

    },[]);

    const toggleTheme = () => {
        const newTheme = theme === "light" ? "dark" : "light";
        setTheme(newTheme);
        localStorage.setItem("app-theme", newTheme); 
    };


   return (
    <ThemeContext.Provider value={{theme, toggleTheme}}>
        {children}
    </ThemeContext.Provider>
);
}

